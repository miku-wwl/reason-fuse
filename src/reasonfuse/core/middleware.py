"""Agent Framework function middleware for the deterministic core."""

from __future__ import annotations

import json
from typing import Any

from agent_framework import FunctionInvocationContext, FunctionMiddleware, MiddlewareTermination
from opentelemetry import trace

from reasonfuse.validation.session_state import emit, json_value

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
    """Map a namespaced Toolbox function to the registry's operation name."""
    return name.split("___", 1)[-1]


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
        engine, raw = self._engine(context)
        tool_name = context.function.name
        # Observability must remain callable after containment so the harness can
        # obtain authoritative state. This is read-only and cannot execute an
        # external operation or bypass the fuse for an operational tool.
        if tool_name == "read_runtime_state":
            await call_next()
            return
        arguments = _arguments(context.arguments)
        core_tool_name = _core_tool_name(tool_name)
        side_effect = core_tool_name in SIDE_EFFECT_TO_RESOURCE
        decision = engine.before_dispatch(core_tool_name, arguments)
        if not decision.allow:
            self._persist(context, engine, raw)
            trace.get_current_span().set_attributes({"reasonfuse.fuse_reason": decision.reason or "",
                                                     "reasonfuse.contract_version": engine.contract.version,
                                                     "reasonfuse.trajectory_state": engine.state.trajectory_state})
            emit("REASONFUSE_FUSE_TRIPPED", tool_name=tool_name, decision=decision.structured_result)
            context.result = decision.structured_result
            raise MiddlewareTermination("ReasonFuse contained the run", result=decision.structured_result)

        verification = engine.pending_verification(core_tool_name, arguments)
        failure = None
        try:
            await call_next()
            tool_result = _result(context.result)
        except MiddlewareTermination:
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
                                    side_effect=side_effect, approved=approved, todo_snapshot=todo)

        if side_effect and approved and tool_result.get("accepted"):
            pending = engine.state.pending_postcondition or {}
            pending["accepted_result"] = tool_result
            engine.state.pending_postcondition = pending
        if verification and engine.state.pending_postcondition:
            pending = engine.state.pending_postcondition
            outcome = OutcomeVerifier().verify(
                pending["action"], pending.get("accepted_result", {}), tool_result,
                requested_resource=pending["resource"],
            )
            engine.set_outcome(outcome)
            tool_result = {"tool_result": tool_result, "outcome": outcome}
        elif side_effect and failure:
            engine.set_outcome({"outcome": "OUTCOME_UNKNOWN", "reason": "side_effect_dispatch_failed"})

        signals = dict(observation.signals)
        if verification:
            signals["postcondition_delta"] = engine.state.last_postcondition_result["outcome"] == "OUTCOME_VERIFIED"
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
