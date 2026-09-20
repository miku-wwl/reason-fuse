"""Responses 2.0.0 entry point; the platform owns transcript and session stores."""

import asyncio
import hashlib
import json
import logging
from contextlib import aclosing

from agent_framework_foundry_hosting import ResponsesHostServer
from azure.ai.agentserver.core import get_request_context
from azure.ai.agentserver.core.storage import FoundryStateStore
from azure.ai.agentserver.core.tasks import set_resilient_tasks_enabled
from azure.ai.agentserver.responses import ResponsesServerOptions
from azure.ai.agentserver.responses.streaming import ResponseEventStream

from reasonfuse.agent import build_agent
from reasonfuse.host_admission import AdmissionRejected, acquire, complete


class ReasonFuseHostServer(ResponsesHostServer):
    """Own session restoration through persistence using native conditional writes."""

    async def _handle_response(self, request, context, cancellation_signal):
        if request.get("store", True) is not True:
            raise ValueError("ReasonFuse Hosted requires store=true for coordinated session ownership")
        # Observe the platform-to-SDK identity boundary without logging user input
        # or opaque caller credentials. Equal digests identify equal scopes.
        def identity(value):
            return hashlib.sha256(str(value).encode()).hexdigest()[:16] if value else None

        logging.getLogger(__name__).info("REASONFUSE_HOST_IDENTITY %s", json.dumps({
            "response": identity(context.response_id),
            "request_conversation": identity(request.get("conversation")),
            "context_conversation": identity(context.conversation_id),
            "previous_response": identity(request.get("previous_response_id")),
            "chain": identity(context.conversation_chain_id),
            "platform_session": identity(get_request_context().session_id),
            "recovery": context.is_recovery,
            "steered": context.is_steered_turn,
        }, sort_keys=True))
        last_sequence = -1
        terminal = None
        try:
            store = await FoundryStateStore.get_or_create(
                "reasonfuse_host_admission_v1", user_isolation=True, item_ttl_seconds=-1,
            )
            async with store:
                admission = await acquire(store, conversation_id=context.conversation_id,
                                          previous_response_id=request.get("previous_response_id"),
                                          response_id=context.response_id)
                # Existing admission must never silently restart an expired or
                # missing AgentSession with a fresh side-effect budget.
                if admission.previous_head:
                    sessions = self._session_storage_provider.get_store(
                        config=self.config, platform_context=get_request_context())
                    load_id = context.conversation_id or request.get("previous_response_id")
                    if await sessions.get(load_id) is None:
                        raise AdmissionRejected("authoritative AgentSession is missing; reconciliation required")
                async with aclosing(super()._handle_response(request, context, cancellation_signal)) as events:
                    async for event in events:
                        last_sequence = event.get("sequence_number", last_sequence)
                        if event.get("type") == "response.completed":
                            # The pinned parent emits this only after session.set
                            # succeeds. Publish ownership before releasing terminal.
                            await complete(store, admission)
                            terminal = event
                        elif event.get("type") in {"response.failed", "response.incomplete"}:
                            terminal = event
                        else:
                            yield event
            if terminal is None:
                raise AdmissionRejected("host ended without a persisted completion")
        except Exception as error:
            logging.getLogger(__name__).error("REASONFUSE_HOST_ADMISSION rejected: %s", type(error).__name__)
            stream = ResponseEventStream(response_id=context.response_id)
            created = stream.emit_created()
            if last_sequence < 0:
                yield created
                last_sequence = created["sequence_number"]
            message = str(error) if isinstance(error, AdmissionRejected) else "admission storage failed; reconciliation required"
            terminal = stream.emit_failed(code="server_error", message="ReasonFuse: " + message)
            terminal["sequence_number"] = last_sequence + 1
        yield terminal


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Native tasks retain their lifecycle role; conditional admission owns the
    # application session. Steering must not cancel an admitted side effect.
    set_resilient_tasks_enabled(True)
    agent = build_agent()
    server = ReasonFuseHostServer(agent, history_source="agent_server",
                                 options=ResponsesServerOptions(steerable_conversations=False))
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
