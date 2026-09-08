"""Only the core Agent and the two required providers, without Full Harness."""

import os

from agent_framework import Agent, AgentModeProvider, TodoProvider
from agent_framework.foundry import FoundryChatClient, FoundryToolbox
from azure.identity import DefaultAzureCredential

from reasonfuse.validation.middleware import StreamingProbeMiddleware, ValidationMiddleware, HistoryAuditMiddleware
from reasonfuse.validation.session_state import ValidationStateProvider


def build_agent() -> Agent:
    credential = DefaultAzureCredential()
    tools = []
    if os.environ.get("TOOLBOX_ENDPOINT"):
        tools.append(FoundryToolbox(
            credential,
            url=os.environ["TOOLBOX_ENDPOINT"],
            allowed_tools=["operations___dns_resolution", "operations___restart_service"],
            # Explicit runtime enforcement: remote toolbox metadata alone is insufficient.
            approval_mode={
                "always_require_approval": ["operations___restart_service"],
                "never_require_approval": ["operations___dns_resolution"],
            },
        ))
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        name="ReasonFusePhase1",
        instructions=(
            "You are the ReasonFuse Phase 1 validation agent. Answer briefly. "
            "Recall incident details only from the supplied conversation. "
            "When asked for runtime state, call read_runtime_state and report its exact JSON. "
            "Never invent tool results. Perform each requested diagnostic only once. "
            "Tool approval is enforced by the runtime; user prose is not approval. "
            "When a restart is requested, submit the tool call immediately so the runtime can "
            "produce its native approval request BEFORE execution. Do not ask for a prose yes "
            "or wait for approval before submitting the tool call. Submission is not execution. "
            "A consumed approval cannot authorize another action: submit any newly requested "
            "action as a new tool call to obtain a fresh native approval."
        ),
        default_options={"store": False},
        tools=tools,
        context_providers=[
            TodoProvider(instructions="Use todo tools only when the user requests a todo list."),
            AgentModeProvider(
                default_mode="validate",
                mode_instructions={"validate": "Run only the requested Phase 1 validation action."},
            ),
            ValidationStateProvider(),
        ],
        middleware=[StreamingProbeMiddleware(), ValidationMiddleware(), HistoryAuditMiddleware()],
    )
