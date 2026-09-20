"""AgentSession provider for the versioned ReasonFuse core state."""

from __future__ import annotations

import json

from agent_framework import ContextProvider, tool
from azure.ai.agentserver.core import get_request_context

from reasonfuse.telemetry import emit
from reasonfuse.config import runtime_configuration
from reasonfuse.runtime import session_locks

from .contract import RunContract
from .state import ReasonFuseState
from .engine import ReasonFuseEngine

CORE_SOURCE_ID = "reasonfuse_core_v1"


def _enabled() -> bool:
    return runtime_configuration().enabled


def _contract() -> RunContract:
    return runtime_configuration().contract


class CoreStateProvider(ContextProvider):
    def __init__(self) -> None:
        runtime_configuration()  # Fail during construction, before model/tool I/O.
        super().__init__(CORE_SOURCE_ID)

    async def before_run(self, *, agent, session, context, state):
        async with session_locks(session).dispatch:
            self._initialize(session, state)
        if context is not None:
            @tool(approval_mode="never_require")
            def read_reasonfuse_state() -> str:
                """Read the active runtime policy and authoritative ReasonFuse state."""
                return json.dumps(session.state[CORE_SOURCE_ID], sort_keys=True)
            context.extend_tools(self.source_id, [read_reasonfuse_state])

    def _initialize(self, session, state):
        config = runtime_configuration()
        if state:
            core = ReasonFuseState.from_dict(state)
            if config.profile == "runtime" and not core.reasonfuse_enabled:
                raise ValueError("A disabled session cannot resume in the runtime profile")
        else:
            core = ReasonFuseState(reasonfuse_enabled=config.enabled)
        contract = config.contract
        if state and (core.run_contract_version != contract.version or
                      (core.contract_limits and core.contract_limits != contract.to_dict())):
            raise ValueError("persisted ReasonFuse contract cannot be changed on resume")
        core.run_contract_version = contract.version
        core.contract_limits = contract.to_dict()
        core.runtime_profile = config.profile
        if core.action_lifecycle and core.action_lifecycle["status"] == "DISPATCHING":
            ReasonFuseEngine(core, contract).set_outcome({
                "outcome": "OUTCOME_UNKNOWN", "reason": "resumed_interrupted_dispatch",
            })
        core.framework_session_id = session.session_id if session else None
        core.agent_session_id = get_request_context().session_id
        core.conversation_id = session.service_session_id if session else None
        state.clear()
        state.update(core.to_dict())
        emit("REASONFUSE_RUN_START", run_id=core.run_id, agent_session_id=core.agent_session_id,
             framework_session_id=core.framework_session_id, contract=contract.to_dict(),
             enabled=core.reasonfuse_enabled, profile=core.runtime_profile)

    async def after_run(self, *, agent, session, context, state):
        emit("REASONFUSE_RUN_END", run_id=state.get("run_id"), contained=state.get("contained"))
