"""Responses 2.0.0 entry point; the platform owns transcript and session stores."""

import asyncio
import logging
from contextlib import aclosing

from agent_framework_foundry_hosting import ResponsesHostServer
from azure.ai.agentserver.core.tasks import set_resilient_tasks_enabled
from azure.ai.agentserver.responses import ResponsesServerOptions

from reasonfuse.agent import build_agent


class ReasonFuseHostServer(ResponsesHostServer):
    """Require the persisted request path covered by native chain coordination."""

    async def _handle_response(self, request, context, cancellation_signal):
        if request.get("store", True) is not True:
            raise ValueError("ReasonFuse Hosted requires store=true for coordinated session ownership")
        async with aclosing(super()._handle_response(request, context, cancellation_signal)) as events:
            async for event in events:
                yield event


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # The pinned host otherwise restores independent sessions without a shared
    # request gate. Native tasks own admission; steering rejects stale forks.
    set_resilient_tasks_enabled(True)
    agent = build_agent()
    server = ReasonFuseHostServer(agent, history_source="agent_server",
                                 options=ResponsesServerOptions(steerable_conversations=True))
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
