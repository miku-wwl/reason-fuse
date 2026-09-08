"""Only the core Agent and the two required providers, without Full Harness."""

import os

from agent_framework import Agent, AgentModeProvider, TodoProvider
from agent_framework.foundry import FoundryChatClient, FoundryToolbox
from azure.identity import DefaultAzureCredential

from reasonfuse.core.middleware import ReasonFuseFunctionMiddleware
from reasonfuse.core.provider import CoreStateProvider
from reasonfuse.validation.middleware import StreamingProbeMiddleware, ValidationMiddleware, HistoryAuditMiddleware
from reasonfuse.validation.session_state import ValidationStateProvider


def build_agent() -> Agent:
    credential = DefaultAzureCredential()
    profile = os.environ.get("REASONFUSE_PROFILE", "phase1").lower()
    phase2 = profile == "phase2"
    tools = []
    if os.environ.get("TOOLBOX_ENDPOINT"):
        tools.append(FoundryToolbox(
            credential,
            url=os.environ["TOOLBOX_ENDPOINT"],
            allowed_tools=[
                "operations___dns_resolution", "operations___restart_service",
                "operations___service_status", "operations___database_health",
                "operations___retrieval_fixture",
            ],
            # Explicit runtime enforcement: remote toolbox metadata alone is insufficient.
            approval_mode={
                "always_require_approval": ["operations___restart_service"],
                "never_require_approval": [
                    "operations___dns_resolution", "operations___service_status",
                    "operations___database_health", "operations___retrieval_fixture",
                ],
            },
        ))
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        name="ReasonFusePhase2" if phase2 else "ReasonFusePhase1",
        instructions=(
            ("You are the ReasonFuse Phase 2 core scenario agent. Use the named tools exactly as requested. "
             "Do not claim an action succeeded without its tool result or postcondition. "
             if phase2 else "You are the ReasonFuse Phase 1 validation agent. Answer briefly. ") +
            "Recall incident details only from the supplied conversation. "
            "When asked for runtime state, call read_runtime_state and report its exact JSON. "
            "Never invent tool results. " +
            ("Perform each requested diagnostic only once. " if not phase2 else "") +
            ("Tool approval is enforced by the runtime; user prose is not approval. "
            "When a restart is requested, submit the tool call immediately so the runtime can "
            "produce its native approval request BEFORE execution. Do not ask for a prose yes "
            "or wait for approval before submitting the tool call. Submission is not execution. "
            "A consumed approval cannot authorize another action: submit any newly requested "
            "action as a new tool call to obtain a fresh native approval."
            if not phase2 else
            "Tool approval is enforced by the runtime; user prose is not approval. "
            "When a restart is requested, submit the tool call immediately for native approval; "
            "submission is not execution. Do not ask for prose approval. A consumed approval cannot "
            "authorize another action: submit a new call for fresh native approval. "
            "Do not stop a requested bounded detector scenario early. ")
        ),
        default_options={"store": False},
        tools=tools,
        context_providers=[
            TodoProvider(instructions="Use todo tools only when the user requests a todo list."),
            AgentModeProvider(
                default_mode="validate",
                mode_instructions={"validate": ("Run the requested bounded Phase 2 core scenario."
                                               if phase2 else "Run only the requested Phase 1 validation action.")},
            ),
            ValidationStateProvider(),
            CoreStateProvider(),
        ],
        middleware=[StreamingProbeMiddleware(), ValidationMiddleware(),
                    ReasonFuseFunctionMiddleware(), HistoryAuditMiddleware()],
    )
