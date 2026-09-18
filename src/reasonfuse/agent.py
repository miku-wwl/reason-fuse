"""Build the single lean ReasonFuse Hosted Agent."""

import os

from agent_framework import Agent, AgentModeProvider, MCPStreamableHTTPTool, TodoProvider
from agent_framework.foundry import FoundryChatClient, FoundryToolbox
from azure.identity import DefaultAzureCredential

from reasonfuse.core.middleware import ReasonFuseFunctionMiddleware
from reasonfuse.core.provider import CoreStateProvider
from reasonfuse.validation.middleware import ValidationMiddleware, HistoryAuditMiddleware
from reasonfuse.validation.session_state import ValidationStateProvider


def build_agent() -> Agent:
    credential = DefaultAzureCredential()
    tools = []
    toolbox_endpoint = os.environ.get("TOOLBOX_ENDPOINT")
    toolbox_name = os.environ.get("TOOLBOX_NAME")
    if toolbox_endpoint or toolbox_name:
        toolbox_options = {"url": toolbox_endpoint} if toolbox_endpoint else {"name": toolbox_name}
        # The Foundry Toolbox definition carries approval metadata, but the
        # hosted Agent Framework MCP adapter also needs the local approval map
        # to emit a native approval request before side effects.  Include both
        # the server's raw names and the Hosted Toolbox namespace used by the
        # Responses tool surface.
        tools.append(FoundryToolbox(
            credential,
            **toolbox_options,
            load_prompts=False,
            approval_mode={
                "always_require_approval": [
                    "operations___restart_service",
                    "operations___reset",
                    "reasonfuse-operations___operations___restart_service",
                    "reasonfuse-operations___operations___reset",
                ],
                "never_require_approval": [
                    "operations___service_status",
                    "reasonfuse-operations___operations___service_status",
                ],
            },
        ))
    iq_endpoint = os.environ.get("FOUNDRY_IQ_MCP_ENDPOINT")
    if iq_endpoint and not (toolbox_endpoint or toolbox_name):
        # Azure AI Search exposes the native Knowledge Base retrieval surface as
        # a streamable MCP server.  The token is acquired per request so a
        # long-lived Hosted Agent does not retain an expired access token.
        def search_header_provider(_request: dict[str, object]) -> dict[str, str]:
            token = credential.get_token("https://search.azure.com/.default")
            return {"Authorization": f"Bearer {token.token}"}

        tools.append(MCPStreamableHTTPTool(
            name="foundry-iq",
            url=iq_endpoint,
            allowed_tools=["knowledge_base_retrieve"],
            approval_mode="never_require",
            load_prompts=False,
            request_timeout=120,
            header_provider=search_header_provider,
            description=(
                "Native Foundry IQ retrieval backed by the version-pinned Azure AI Search "
                "Knowledge Base. Use knowledge_base_retrieve for grounded policy answers."
            ),
        ))
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            credential=credential,
        ),
        name="ReasonFuse",
        instructions=(
            "You are the ReasonFuse Hosted Agent. Use named tools exactly as requested. "
            "Do not claim an action succeeded without its tool result or a fresh postcondition. "
            "Recall incident details only from the supplied conversation. "
            "When asked for runtime state, call read_runtime_state and report its exact JSON. "
            "Never invent tool results. "
            + (
                "For Operations validation, use operations___service_status for fresh reads and "
                "operations___restart_service only for an explicitly approved restart. "
                if toolbox_endpoint or toolbox_name else ""
            )
            + (
                "For questions about ReasonFuse policy or containment, call the native "
                "knowledge_base_retrieve tool exactly once and ground the answer in its "
                "returned source/citation. "
                if iq_endpoint else ""
            )
            + "Tool approval is enforced by the runtime; user prose is not approval. "
            "When a side-effecting action is requested, submit the tool call immediately for "
            "native approval. Submission is not execution, and accepted execution is not verified "
            "success. Require a fresh postcondition check before claiming success."
        ),
        default_options={"store": False},
        tools=tools,
        context_providers=[
            TodoProvider(instructions="Use todo tools only when the user requests a todo list."),
            AgentModeProvider(default_mode="validate", mode_instructions={
                "validate": "Run only the requested bounded ReasonFuse validation action."
            }),
            ValidationStateProvider(),
            CoreStateProvider(),
        ],
        middleware=[ValidationMiddleware(), ReasonFuseFunctionMiddleware(), HistoryAuditMiddleware()],
    )
