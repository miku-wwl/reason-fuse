"""Agent Framework function middleware for the deterministic core."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from agent_framework import FunctionInvocationContext, FunctionMiddleware, FunctionTool, MiddlewareTermination
from opentelemetry import trace

from reasonfuse.telemetry import emit, json_value
from reasonfuse.runtime import CURRENT_TURN, session_locks

from .contract import RunContract
from .engine import ReasonFuseEngine, SIDE_EFFECT_TO_RESOURCE
from .outcome import OutcomeVerifier
from .state import ReasonFuseState


def _arguments(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return dict(value or {})


def _result(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        # FoundryToolbox commonly returns one or more Agent Framework Content
        # objects. Normalize the JSON carried by the text content before the
        # core evaluates evidence/retrieval/postcondition signals.
        for item in value:
            text = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
            if not isinstance(text, str):
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    if hasattr(value, "text"):
        value = value.text
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            return {"text": value}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return {"value": json_value(value)}


def _core_tool_name(name: str) -> str:
    """Map local or multi-prefixed Toolbox names to the registry operation."""
    # Local tools use ``operations___restart_service``.  Foundry Toolbox can
    # add its server label as another namespace, producing
    # ``reasonfuse-operations___operations___restart_service``.  The core
    # registry must receive the final operation segment in both cases.
    return name.rsplit("___", 1)[-1]


class ReasonFuseFunctionMiddleware(FunctionMiddleware):
    """Check every native function dispatch and terminate a tripped run."""

    def _engine(self, context: FunctionInvocationContext) -> tuple[ReasonFuseEngine, dict[str, Any]]:
        if context.session is None:
            raise RuntimeError("ReasonFuse requires an AgentSession")
        raw = context.session.state.setdefault("reasonfuse_core_v1", {})
        if not raw:
            raise RuntimeError("CoreStateProvider must initialize the run before dispatch")
        state = ReasonFuseState.from_dict(raw)
        contract = RunContract.from_dict(state.contract_limits) if state.contract_limits else RunContract(
            version=state.run_contract_version
        )
        engine = ReasonFuseEngine(state, contract)
        return engine, raw

    @staticmethod
    def _persist(context: FunctionInvocationContext, engine: ReasonFuseEngine, raw: dict[str, Any]) -> None:
        raw.clear()
        raw.update(engine.state.to_dict())

    async def process(self, context: FunctionInvocationContext, call_next):
        # A tool batch is concurrent in Agent Framework. Load the snapshot only
        # after acquiring the lock and hold it through reservation, I/O and save.
        async with session_locks(context.session).dispatch:
            try:
                await self._process_locked(context, call_next)
            except BaseException:
                # Include normalization/accounting failures after the actual I/O.
                # A blocked sibling must leave an unconsumed obligation intact.
                engine, raw = self._engine(context)
                lifecycle = engine.state.action_lifecycle or {}
                pending = engine.state.pending_postcondition or {}
                if (lifecycle.get("status") == "DISPATCHING"
                        or pending.get("consumed") and not engine.state.last_postcondition_result):
                    engine.set_outcome({"outcome": "OUTCOME_UNKNOWN", "reason": "accounting_interrupted"})
                    self._persist(context, engine, raw)
                raise

    async def _process_locked(self, context: FunctionInvocationContext, call_next):
        engine, raw = self._engine(context)
        turn = CURRENT_TURN.get()
        if turn is not None:
            turn.tools.update({item.name: item for item in context.tools or [] if isinstance(item, FunctionTool)})
        tool_name = context.function.name
        # Observability must remain callable after containment so the harness can
        # obtain authoritative state. This is read-only and cannot execute an
        # external operation or bypass the fuse for an operational tool.
        if tool_name in {"read_runtime_state", "read_reasonfuse_state"}:
            await call_next()
            return
        arguments = _arguments(context.arguments)
        core_tool_name = _core_tool_name(tool_name)
        side_effect = core_tool_name in SIDE_EFFECT_TO_RESOURCE
        if side_effect and not engine._resource(core_tool_name, arguments):
            raise ValueError("A side effect requires a nonempty resource identity")
        decision = engine.before_dispatch(core_tool_name, arguments)
        if not decision.allow:
            if side_effect:
                engine.state.last_proposal = {
                    "status": "BLOCKED", "action": core_tool_name,
                    "resource": engine._resource(core_tool_name, arguments), "reason": decision.reason,
                }
            self._persist(context, engine, raw)
            trace.get_current_span().set_attributes({"reasonfuse.fuse_reason": decision.reason or "",
                                                     "reasonfuse.contract_version": engine.contract.version,
                                                     "reasonfuse.trajectory_state": engine.state.trajectory_state})
            emit("REASONFUSE_FUSE_TRIPPED", tool_name=tool_name, decision=decision.structured_result)
            context.result = decision.structured_result
            raise MiddlewareTermination("ReasonFuse contained the run", result=decision.structured_result)

        verification = engine.pending_verification(core_tool_name, arguments)
        engine.begin_dispatch(core_tool_name, arguments, call_id=context.metadata.get("call_id"))
        if side_effect:
            engine.state.action_lifecycle["tool_name"] = tool_name
        self._persist(context, engine, raw)
        failure = None
        try:
            await call_next()
            tool_result = _result(context.result)
        except (asyncio.CancelledError, KeyboardInterrupt, SystemExit, MiddlewareTermination):
            # A sync tool may still be running in its worker thread. Never infer
            # rollback from cancellation: retain the reserved attempt and contain.
            if side_effect or verification:
                engine.set_outcome({"outcome": "OUTCOME_UNKNOWN", "reason": "dispatch_interrupted"})
            self._persist(context, engine, raw)
            raise
        except Exception as error:
            failure = error
            engine.state.failed_call_count += 1
            tool_result = {"status": "timeout" if isinstance(error, TimeoutError) else "unavailable"}
        approved = context.metadata.get("approval_response") is None or bool(
            getattr(context.metadata.get("approval_response"), "approved", True)
        )
        todo_state = context.session.state.get("todo", {})
        todo = {str(item["id"]): item.get("status") for item in todo_state.get("items", [])}
        observation = engine.record(core_tool_name, arguments, tool_result, executed=True,
                                    side_effect=side_effect, approved=approved, todo_snapshot=todo, reserved=True)

        if verification and engine.state.pending_postcondition:
            pending = engine.state.pending_postcondition
            outcome = OutcomeVerifier().verify(
                pending["action"], pending.get("accepted_result", {}), tool_result,
                requested_resource=pending["resource"],
            )
            engine.set_outcome(outcome)
            tool_result = {"tool_result": tool_result, "outcome": outcome}
        elif side_effect and (failure or tool_result.get("accepted") is not True):
            engine.set_outcome({"outcome": "OUTCOME_UNKNOWN", "reason": "side_effect_not_confirmed_accepted"})

        signals = dict(observation.signals)
        if verification:
            signals["postcondition_delta"] = engine.state.last_postcondition_result["outcome"] == "OUTCOME_VERIFIED"
            context.result = tool_result
        engine.state.last_signals = signals
        self._persist(context, engine, raw)
        attributes = {f"reasonfuse.{key}": value for key, value in signals.items()}
        attributes.update({"reasonfuse.trajectory_state": engine.state.trajectory_state,
                           "reasonfuse.progress_state": engine.state.progress_state,
                           "reasonfuse.fuse_reason": engine.state.fuse_reason or "",
                           "reasonfuse.failure_type": engine.state.fuse_reason or ("TOOL_ERROR" if failure else ""),
                           "reasonfuse.contract_version": engine.contract.version})
        trace.get_current_span().set_attributes(attributes)
        trace.get_current_span().add_event("reasonfuse.observation", attributes)
        emit("REASONFUSE_OBSERVATION", tool_name=tool_name, run_id=engine.state.run_id,
             step=engine.state.step_index, signals=signals, attributes=attributes)
        if engine.state.contained:
            context.result = {"decision": "COMPLETE_AND_CONTAIN", "executed": True,
                              "tool_result": tool_result, "fuse_reason": engine.state.fuse_reason,
                              "step": engine.state.step_index}
            raise MiddlewareTermination("ReasonFuse contained the run after observation", result=context.result)
        if failure:
            raise failure
