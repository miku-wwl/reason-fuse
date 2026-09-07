"""Provider state only: no local transcript, approval store or session manager."""

import json
import logging
import os
import platform
from datetime import datetime, timezone
from importlib.metadata import version

from agent_framework import Content, ContextProvider, tool
from azure.ai.agentserver.core import get_request_context
from opentelemetry import trace

LOG = logging.getLogger("reasonfuse.validation")


def json_value(value):
    if isinstance(value, Content):
        # Tool text is sufficient evidence; omit transport metadata and embedded schemas.
        return {"type": value.type, "text": value.text}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


def emit(event: str, **fields) -> None:
    span = trace.get_current_span().get_span_context()
    LOG.info(json.dumps({
        "event": event,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "trace_id": format(span.trace_id, "032x") if span.is_valid else None,
        **fields,
    }, default=json_value, sort_keys=True))


class ValidationStateProvider(ContextProvider):
    def __init__(self):
        super().__init__("reasonfuse")

    async def before_run(self, *, agent, session, context, state):
        restored = "reasonfuse_test_state" in state
        state.setdefault("reasonfuse_test_state", "RF-STATE-001")
        # Set before any approval can be requested; never repair a changed value.
        state.setdefault("reasonfuse_test_counter", 7)
        state["turn_number"] = state.get("turn_number", 0) + 1
        state["restored_at_turn_start"] = restored
        state["input_message_count"] = len(context.input_messages)

        def snapshot():
            return {
                **state,
                "agent_session_id": session.session_id,
                "platform_session_id": get_request_context().session_id,
                "release_role": os.environ.get("RELEASE_ROLE", "stable"),
                "python_version": platform.python_version(),
                "package_versions": {name: version(name) for name in (
                    "agent-framework-core", "agent-framework-foundry", "agent-framework-foundry-hosting",
                    "azure-ai-projects", "azure-identity", "azure-ai-agentserver-responses",
                )},
            }

        @tool(approval_mode="never_require")
        def read_runtime_state() -> str:
            """Read validation state and release role directly from the current AgentSession."""
            result = snapshot()
            emit("RUNTIME_STATE", **result)
            return json.dumps(result, sort_keys=True)

        context.extend_tools(self.source_id, [read_runtime_state])
        emit("TURN_START", **snapshot())

    async def after_run(self, *, agent, session, context, state):
        emit("TURN_END", agent_session_id=session.session_id, **state)
