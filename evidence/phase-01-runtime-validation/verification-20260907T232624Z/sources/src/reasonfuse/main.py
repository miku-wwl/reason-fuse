"""Responses 2.0.0 entry point; the platform owns transcript and session stores."""

import asyncio
import logging

from agent_framework_foundry_hosting import ResponsesHostServer

from reasonfuse.agent import build_agent


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    agent = build_agent()
    server = ResponsesHostServer(agent, history_source="agent_server")
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
