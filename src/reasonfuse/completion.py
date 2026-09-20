"""Deterministic operational completion before output or history is released.

The persistence gate and approval-binding reader are version-pinned Agent
Framework integration seams. No replacement approval store is introduced.
"""

from __future__ import annotations

import asyncio
import json

from agent_framework import (
    AgentMiddleware, AgentResponse, AgentResponseUpdate, AgentSession, Content,
    FunctionInvocationContext, Message, MiddlewareTermination, ResponseStream,
)
from agent_framework._sessions import _RunPersistenceGate
from agent_framework._tools import _bind_approval_response_to_pending_request, _get_tool_map

from .core.engine import SIDE_EFFECT_TO_RESOURCE
from .core.middleware import ReasonFuseFunctionMiddleware, _core_tool_name
from .core.outcome import PostconditionRegistry
from .core.state import ReasonFuseState
from .runtime import CURRENT_TURN, RuntimeTurn, session_locks

CORE_KEY = "reasonfuse_core_v1"
VERIFICATION_TIMEOUT_SECONDS = 10.0


class ReasonFuseCompletionMiddleware(AgentMiddleware):
    """Buffer a whole turn, settle obligations, then publish runtime-owned output."""

    async def process(self, context, call_next):
        # RawAgent otherwise creates a private session later, invisible at this
        # boundary. Supply one here so tools, providers and output share authority.
        if context.session is None:
            context.session = AgentSession()
        async with session_locks(context.session).run:
            if context.agent.require_per_service_call_history_persistence:
                raise ValueError("ReasonFuse supports run-end history persistence only")
            turn = RuntimeTurn()
            token = CURRENT_TURN.set(turn)
            gate = _RunPersistenceGate()
            context._run_persistence_gate = gate
            denied = self._bound_denials(context)
            try:
                with gate:
                    await call_next()
                    if context.stream:
                        inner = context.result
                        if not isinstance(inner, ResponseStream):
                            raise TypeError("ReasonFuse requires a native ResponseStream")
                        # Drain internally. No original update reaches the consumer.
                        final = await inner.get_final_response()
                    else:
                        final = context.result
                if not isinstance(final, AgentResponse):
                    raise TypeError("ReasonFuse requires a native AgentResponse")
                turn.tools.update(_get_tool_map(context._resolve_run_start_tools()))
                await self._complete(context, turn, denied, final)
                # The provider's response reference is mutated in-place, so its
                # deferred history write sees only the permitted messages.
                await gate.flush()
                if context.stream:
                    async def released():
                        for message in final.messages:
                            yield AgentResponseUpdate(
                                role=message.role, contents=list(message.contents),
                                message_id=message.message_id, author_name=message.author_name,
                                response_id=final.response_id,
                            )
                        yield AgentResponseUpdate(
                            contents=[Content.from_usage(final.usage_details)] if final.usage_details else [],
                            response_id=final.response_id, agent_id=final.agent_id,
                            created_at=final.created_at, finish_reason=final.finish_reason,
                        )
                    context.result = ResponseStream(released(), finalizer=lambda _updates: final)
                else:
                    context.result = final
            except BaseException:
                gate.drop()
                # This also covers a model/stream interruption *after* acceptance,
                # before completion-time verification could be attempted.
                self._abandon_pending(context.session, "completion_interrupted")
                context.result = None
                raise
            finally:
                CURRENT_TURN.reset(token)

    @staticmethod
    def _bound_denials(context) -> list[dict]:
        denied = []
        for message in context.messages:
            for content in message.contents:
                if content.type != "function_approval_response":
                    continue
                # Read the framework's binding without consuming or rewriting it.
                # The native invocation layer remains the sole approval authority.
                bound = _bind_approval_response_to_pending_request(content, context.session, consume=False)
                if bound is None or bound.approved is not False or bound.function_call is None:
                    continue
                call = bound.function_call
                action = _core_tool_name(call.name)
                if action in SIDE_EFFECT_TO_RESOURCE:
                    args = call.parse_arguments() or {}
                    denied.append({"status": "DENIED", "action": action,
                                   "resource": args.get(SIDE_EFFECT_TO_RESOURCE[action]),
                                   "approval_id": bound.id})
        return denied

    @staticmethod
    def _abandon_pending(session, reason):
        raw = session.state.get(CORE_KEY)
        if not raw:
            return
        middleware = ReasonFuseFunctionMiddleware()
        context = FunctionInvocationContext(None, {}, session=session)
        engine, raw = middleware._engine(context)
        lifecycle = engine.state.action_lifecycle or {}
        if (lifecycle.get("status") in {"DISPATCHING", "VERIFICATION_PENDING"}
                or engine.state.pending_postcondition and not engine.state.last_postcondition_result):
            engine.set_outcome({"outcome": "OUTCOME_UNKNOWN", "reason": reason})
            middleware._persist(context, engine, raw)

    async def _verify(self, session, turn, final):
        raw = session.state[CORE_KEY]
        pending = raw.get("pending_postcondition")
        if not pending or pending.get("consumed") or raw.get("last_postcondition_result"):
            return
        if raw["contained"]:
            self._abandon_pending(session, "verification_blocked_by_containment")
            return
        registered = PostconditionRegistry().get(pending["action"])
        original_name = (raw.get("action_lifecycle") or {}).get("tool_name")
        expected_name = (original_name.rsplit("___", 1)[0] + "___" + registered.verifier_tool
                         if original_name and "___" in original_name else registered.verifier_tool)
        candidates = [item for name, item in turn.tools.items() if name == expected_name]
        if not original_name:
            candidates = [item for name, item in turn.tools.items()
                          if _core_tool_name(name) == registered.verifier_tool]
        if len(candidates) != 1 or candidates[0].approval_mode != "never_require":
            self._abandon_pending(session, "registered_verifier_unavailable")
            return
        verifier = candidates[0]
        args = {registered.resource_argument: pending["resource"]}
        call_id = f"{raw['run_id']}-verify-{raw['step_index'] + 1}"
        invocation = FunctionInvocationContext(verifier, args, session=session, tools=list(turn.tools.values()))
        invocation.metadata["call_id"] = call_id

        async def call_next():
            invocation.result = await verifier.invoke(arguments=args, context=invocation, tool_call_id=call_id)

        try:
            async with asyncio.timeout(VERIFICATION_TIMEOUT_SECONDS):
                await ReasonFuseFunctionMiddleware().process(invocation, call_next)
        except MiddlewareTermination:
            # FAILED/UNKNOWN are normal deterministic terminal outcomes. A
            # pre-dispatch block, however, cannot stand in for verification.
            self._abandon_pending(session, "registered_verification_blocked")
        except Exception:
            self._abandon_pending(session, "registered_verification_unavailable")
        if invocation.result is not None:
            final.messages.extend([
                Message("assistant", [Content.from_function_call(call_id, verifier.name, arguments=args)]),
                Message("tool", [Content.from_function_result(call_id, result=invocation.result)]),
            ])
        self._abandon_pending(session, "registered_verification_incomplete")

    async def _complete(self, context, turn, denied, final):
        session = context.session
        raw = session.state[CORE_KEY]
        if not raw["reasonfuse_enabled"]:
            return  # Explicit evaluation OFF; native approval still applies.
        if denied:
            raw["denied_proposal_count"] += len(denied)
            raw["last_proposal"] = denied[-1]
        approvals = [c for m in final.messages for c in m.contents if c.type == "function_approval_request"]
        for approval in approvals:
            call = approval.function_call
            if call and _core_tool_name(call.name) in SIDE_EFFECT_TO_RESOURCE:
                args = call.parse_arguments() or {}
                raw["last_proposal"] = {
                    "status": "APPROVAL_REQUIRED", "action": _core_tool_name(call.name),
                    "resource": args.get(SIDE_EFFECT_TO_RESOURCE[_core_tool_name(call.name)]),
                    "approval_id": approval.id,
                }
        await self._verify(session, turn, final)
        core = ReasonFuseState.from_dict(session.state[CORE_KEY])
        if not (core.action_lifecycle or core.last_proposal or core.pending_postcondition):
            return
        # Preserve native tool/approval contents and their occurrence IDs. Remove
        # ALL model-authored answer/reasoning content for operational sessions;
        # no string matching or model-based success classifier is involved.
        kept = []
        for message in final.messages:
            if str(message.role) == "assistant":
                message.raw_representation = None
                message.contents[:] = [c for c in message.contents if c.type in {
                    "function_call", "function_approval_request", "function_result",
                }]
            if message.contents:
                kept.append(message)
        lifecycle = core.action_lifecycle or {}
        proposal = core.last_proposal or {}
        outcome = (proposal.get("status") or
                   (core.last_postcondition_result or {}).get("outcome") or "OUTCOME_UNKNOWN")
        payload = {
            "outcome": outcome, "action_lifecycle": core.action_lifecycle,
            "proposal": core.last_proposal, "postcondition": core.last_postcondition_result,
            "side_effect_count": core.side_effect_count, "contained": core.contained,
        }
        if lifecycle.get("status") == "ACCEPTED":
            payload["outcome"] = "ACCEPTED_UNVERIFIED"
        kept.append(Message("assistant", [json.dumps(payload, sort_keys=True)]))
        final.messages[:] = kept
        final.raw_representation = None
        # A parsed structured model answer is another output surface in 1.17.0.
        final._value = payload
        final._value_parsed = True
        final._response_format = None
