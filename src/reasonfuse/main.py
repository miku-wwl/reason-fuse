"""Responses 2.0.0 entry point; the platform owns transcript and session stores."""

import asyncio
import logging

from agent_framework_foundry_hosting import ResponsesHostServer

from reasonfuse.agent import build_agent
from reasonfuse.telemetry import (
    configure_reasonfuse_log_exporter,
    flush_reasonfuse_log_exporter,
    reasonfuse_log_extra,
    shutdown_reasonfuse_log_exporter,
)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    exporter = configure_reasonfuse_log_exporter()
    if exporter:
        logging.getLogger("reasonfuse.validation").info(
            "REASONFUSE_TRACE_EXPORTER_READY",
            extra=reasonfuse_log_extra("REASONFUSE_TRACE_EXPORTER_READY", {"release_role": "startup"}),
        )
        flush_reasonfuse_log_exporter()
    try:
        agent = build_agent()
        server = ResponsesHostServer(agent, history_source="agent_server")
        await server.run_async()
    finally:
        shutdown_reasonfuse_log_exporter(exporter)


if __name__ == "__main__":
    asyncio.run(main())
