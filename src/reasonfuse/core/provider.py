"""AgentSession provider for the versioned ReasonFuse core state."""

from __future__ import annotations

import json
import os

from agent_framework import ContextProvider
from azure.ai.agentserver.core import get_request_context

from reasonfuse.validation.session_state import emit

from .contract import RunContract
from .state import ReasonFuseState

CORE_SOURCE_ID = "reasonfuse_core_v1"


def _enabled() -> bool:
    value = os.environ.get("REASONFUSE_ENABLED", "false").strip().lower()
    if value not in {"true", "false"}:
        raise ValueError("REASONFUSE_ENABLED must be true or false")
    return value == "true"


def _contract() -> RunContract:
    raw = os.environ.get("REASONFUSE_CONTRACT_JSON")
    if not raw:
        return RunContract()
    return RunContract.from_dict(json.loads(raw))


class CoreStateProvider(ContextProvider):
    def __init__(self) -> None:
        super().__init__(CORE_SOURCE_ID)

    async def before_run(self, *, agent, session, context, state):
        if state:
            core = ReasonFuseState.from_dict(state)
        else:
            core = ReasonFuseState(reasonfuse_enabled=_enabled())
        contract = _contract()
        if state and (core.run_contract_version != contract.version or
                      (core.contract_limits and core.contract_limits != contract.to_dict())):
            raise ValueError("persisted ReasonFuse contract cannot be changed on resume")
        core.run_contract_version = contract.version
        core.contract_limits = contract.to_dict()
        core.reasonfuse_enabled = core.reasonfuse_enabled if state else _enabled()
        core.framework_session_id = session.session_id if session else None
        core.agent_session_id = get_request_context().session_id
        core.conversation_id = session.service_session_id if session else None
        state.clear()
        state.update(core.to_dict())
        emit("REASONFUSE_RUN_START", run_id=core.run_id, agent_session_id=core.agent_session_id,
             framework_session_id=core.framework_session_id, contract=contract.to_dict())

    async def after_run(self, *, agent, session, context, state):
        emit("REASONFUSE_RUN_END", run_id=state.get("run_id"), contained=state.get("contained"))
