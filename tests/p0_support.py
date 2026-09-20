"""Scripted model transport for native-framework regressions; no model/network."""

from unittest.mock import patch

from agent_framework import (
    BaseChatClient, ChatMiddlewareLayer, ChatResponse, ChatResponseUpdate,
    Content, FunctionInvocationLayer, Message, ResponseStream,
)

from reasonfuse.agent import build_agent

UNSUPPORTED_SUCCESS = "The orders restart completed successfully. UNSUPPORTED_MODEL_CLAIM"


def call(identifier="restart-1", name="operations___restart_service", resource="orders"):
    return Content.from_function_call(identifier, name, arguments={"service_name": resource})


class ScriptedClient(FunctionInvocationLayer, ChatMiddlewareLayer, BaseChatClient):
    def __init__(self, batches):
        super().__init__()
        self.batches = list(batches)
        self.requests = []

    def _inner_get_response(self, *, messages, stream, options, **kwargs):
        self.requests.append([m.to_dict() for m in messages])
        contents = self.batches.pop(0)
        response_id = f"script-{len(self.requests)}"
        if stream:
            async def updates():
                if isinstance(contents, BaseException):
                    yield ChatResponseUpdate(role="assistant", contents=[Content.from_text(UNSUPPORTED_SUCCESS)],
                                             response_id=response_id, message_id=response_id)
                    raise contents
                for content in contents:
                    yield ChatResponseUpdate(role="assistant", contents=[content],
                                             response_id=response_id, message_id=response_id)
            return ResponseStream(updates(), finalizer=ChatResponse.from_updates)

        async def response():
            if isinstance(contents, BaseException):
                raise contents
            return ChatResponse(messages=[Message("assistant", contents)], response_id=response_id)
        return response()


def make_agent(batches, tools):
    client = ScriptedClient(batches)
    with patch("reasonfuse.agent.FoundryChatClient", return_value=client), patch("reasonfuse.agent.DefaultAzureCredential"):
        agent = build_agent()
    agent.default_options["tools"] = list(tools)
    return agent, client


def approvals(response):
    return [c for m in response.messages for c in m.contents if c.type == "function_approval_request"]


def approval_message(response, approved=True):
    return Message("user", [c.to_function_approval_response(approved=approved) for c in approvals(response)])
