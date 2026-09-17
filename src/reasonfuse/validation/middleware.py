"""Observe function calls and deny the specified hostname before dispatch."""

from collections.abc import Mapping
import json

from agent_framework import (
    ChatMiddleware, FunctionInvocationContext, FunctionMiddleware,
)

from reasonfuse.validation.session_state import emit, json_value, message_summary


class HistoryAuditMiddleware(ChatMiddleware):
    """Observe actual model-bound inputs/options without modifying the request."""

    async def process(self, context, call_next):
        if context.session:
            state = context.session.state.setdefault("reasonfuse", {})
            if state.get("history_audit"):
                entry = {"store": (context.options or {}).get("store"),
                         "service_session_id": context.session.service_session_id,
                         "messages": [message_summary(message) for message in context.messages]}
                state.setdefault("chat_requests", []).append(entry)
                emit("MODEL_REQUEST_AUDIT", **entry)
        await call_next()


def contains_blocked_hostname(value) -> bool:
    if isinstance(value, Mapping):
        return any(
            (key == "hostname" and item == "blocked.reasonfuse.local")
            or contains_blocked_hostname(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(contains_blocked_hostname(item) for item in value)
    return False


class ValidationMiddleware(FunctionMiddleware):
    async def process(self, context: FunctionInvocationContext, call_next):
        args = context.arguments
        args = args.model_dump() if hasattr(args, "model_dump") else dict(args)
        fields = {
            "tool_name": context.function.name,
            "arguments": args,
            "agent_session_id": context.session.session_id if context.session else None,
        }
        def record(event, result=None):
            if context.session:
                state = context.session.state.setdefault("reasonfuse", {})
                events = state.setdefault("middleware_events", [])
                events.append({"event": event, **fields, "result": json.dumps(result, default=json_value)[:4096] if result is not None else None})
                del events[:-20]
        emit("BEFORE", **fields)
        record("BEFORE")
        if contains_blocked_hostname(args):
            context.result = {"status": "BLOCKED", "reason": "validation_hostname_rule"}
            emit("BLOCK", **fields)
            record("BLOCK", context.result)
            return
        await call_next()
        emit("AFTER", **fields, result=context.result)
        record("AFTER", context.result)
