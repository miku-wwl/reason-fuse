"""Real pinned host, native session restoration and independent accepting backend.

No model/network calls; native tasks are disabled so their scheduling cannot mask
an admission defect. These local storage tests do not establish cloud CAS semantics.
"""

import asyncio
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import httpx
from agent_framework import Content, tool
from agent_framework_foundry_hosting._state_store import FoundryAgentSessionStore
from azure.ai.agentserver.core import get_request_context
from azure.ai.agentserver.core.storage import FoundryStateStore
from azure.ai.agentserver.core.tasks import set_resilient_tasks_enabled
from azure.ai.agentserver.responses._id_generator import IdGenerator

from p0_support import UNSUPPORTED_SUCCESS, call, make_agent
from reasonfuse.host_admission import AdmissionRejected, acquire, complete
from reasonfuse.main import ReasonFuseHostServer


class HostAdmissionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        env = patch.dict(os.environ, {"AGENTSERVER_STATE_ROOT": temp.name,
            "FOUNDRY_PROJECT_ENDPOINT": "https://test.invalid/api/projects/test",
            "AZURE_AI_PROJECT_ENDPOINT": "https://test.invalid/api/projects/test",
            "AZURE_AI_MODEL_DEPLOYMENT_NAME": "scripted",
            "TOOLBOX_NAME": ""}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        set_resilient_tasks_enabled(False)
        self.entered, self.release = asyncio.Event(), asyncio.Event()
        self.attempts = 0
        self.restored = []

        @tool(name="operations___restart_service", approval_mode="always_require")
        async def restart(service_name: str) -> str:
            """Restart the service; every call is accepted, with no backend deduplication."""
            self.attempts += 1
            self.entered.set()
            await self.release.wait()
            return '{"accepted":true,"generation":"g2"}'

        @tool(name="operations___service_status", approval_mode="never_require")
        async def status(service_name: str) -> str:
            """Read fresh service health."""
            return '{"resource":"orders","generation":"g2","service_health":"HEALTHY"}'

        agent, self.model = make_agent([[call()]] + [[Content.from_text(UNSUPPORTED_SUCCESS)]] * 5,
                                      [restart, status])
        self.host = ReasonFuseHostServer(agent, history_source="agent_server", configure_observability=None)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.host), base_url="http://localhost")
        self.addAsyncCleanup(self.client.aclose)
        self.addCleanup(self.release.set)

    async def request(self, body):
        response = await self.client.post("/responses", json={"store": True, **body})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    async def pending(self, explicit=True):
        conversation = IdGenerator.new_id("conv") if explicit else None
        body = {"input": "Restart orders"}
        if conversation:
            body["conversation"] = conversation
        result = await self.request(body)
        self.assertEqual(result["status"], "completed", result)
        approval = next(i for i in result["output"] if i["type"] == "mcp_approval_request")
        follow = {"input": [{"type": "mcp_approval_response", "approval_request_id": approval["id"], "approve": True}]}
        follow["conversation" if explicit else "previous_response_id"] = conversation or result["id"]
        return result, follow

    async def test_explicit_overlap_rejected_before_independent_restore(self):
        await self.check_overlap(explicit=True)

    async def test_previous_response_overlap_and_stale_head(self):
        await self.check_overlap(explicit=False)

    async def check_overlap(self, explicit):
        initial, follow = await self.pending(explicit)
        original_get = FoundryAgentSessionStore.get

        async def observe(store, key):
            value = await original_get(store, key)
            if value:
                self.restored.append(value)
            return value

        with patch.object(FoundryAgentSessionStore, "get", observe):
            first = asyncio.create_task(self.request(follow))
            await asyncio.wait_for(self.entered.wait(), 3)
            rejected = await self.request(follow)
            self.assertEqual(rejected["status"], "failed", rejected)
            self.assertEqual(self.attempts, 1)
            # Preflight and parent each restore a distinct live Python session;
            # neither the local session lock nor backend dedup protects this test.
            self.assertEqual(len(self.restored), 2)
            self.assertIsNot(self.restored[0], self.restored[1])
            self.release.set()
            accepted = await first
        self.assertEqual(accepted["status"], "completed", accepted)
        self.assertIn("OUTCOME_VERIFIED", json.dumps(accepted))
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(accepted))
        key = follow.get("conversation") or accepted["id"]
        saved = await FoundryAgentSessionStore(get_request_context()).get(key)
        core = saved.state["reasonfuse_core_v1"]
        self.assertEqual(core["side_effect_count"], 1)
        self.assertEqual(core["action_lifecycle"]["status"], "VERIFIED")
        if not explicit:
            stale = await self.request(follow)
            self.assertEqual(stale["status"], "failed")
            self.assertIn("stale continuation", stale["error"]["message"])
        self.assertEqual(self.attempts, 1)

    async def test_cancelled_dispatch_retains_busy_admission(self):
        _, follow = await self.pending()
        active = asyncio.create_task(self.request(follow))
        await asyncio.wait_for(self.entered.wait(), 3)
        active.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await active
        blocked = await self.request(follow)
        self.assertEqual(blocked["status"], "failed")
        self.assertEqual(self.attempts, 1)

    async def test_session_save_failure_does_not_release_authority(self):
        _, follow = await self.pending()
        self.release.set()
        with patch.object(FoundryAgentSessionStore, "set", side_effect=OSError("save failed")):
            failed = await self.request(follow)
        self.assertEqual(failed["status"], "failed")
        blocked = await self.request(follow)
        self.assertEqual(blocked["status"], "failed")
        self.assertEqual(self.attempts, 1)

    async def test_missing_session_cannot_reset_budget(self):
        _, follow = await self.pending()
        await FoundryAgentSessionStore(get_request_context()).delete(follow["conversation"])
        result = await self.request(follow)
        self.assertEqual(result["status"], "failed")
        self.assertIn("AgentSession is missing", result["error"]["message"])
        self.assertEqual(self.attempts, 0)

    async def test_admission_commit_failure_withholds_completed_terminal(self):
        _, follow = await self.pending()
        self.release.set()
        with patch("reasonfuse.main.complete", side_effect=OSError("head write failed")):
            failed = await self.request(follow)
        self.assertEqual(failed["status"], "failed")
        self.assertIn("admission storage failed", failed["error"]["message"])
        self.assertEqual((await self.request(follow))["status"], "failed")
        self.assertEqual(self.attempts, 1)

    async def test_unknown_previous_chain_and_storage_failure_fail_closed(self):
        result = await self.request({"previous_response_id": IdGenerator.new_response_id(), "input": "Restart orders"})
        self.assertEqual(result["status"], "failed")
        with patch("reasonfuse.main.FoundryStateStore.get_or_create", side_effect=OSError("unavailable")):
            result = await self.request({"input": "Restart orders"})
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(self.model.requests), 0)

    async def test_conditional_writes_reject_same_snapshot_and_release_failure(self):
        store = await FoundryStateStore.get_or_create("cas-test", item_ttl_seconds=-1)
        async with store:
            first = await acquire(store, conversation_id="conv-test", previous_response_id=None, response_id="head")
            await complete(store, first)
            original_get = store.get_item
            entered = 0
            both_read = asyncio.Event()

            async def same_snapshot(key):
                nonlocal entered
                value = await original_get(key)
                entered += 1
                if entered == 2:
                    both_read.set()
                await both_read.wait()
                return value

            with patch.object(store, "get_item", same_snapshot):
                results = await asyncio.gather(*[acquire(store, conversation_id="conv-test",
                    previous_response_id=None, response_id=label) for label in ["a", "b"]], return_exceptions=True)
            self.assertEqual(sum(isinstance(r, AdmissionRejected) for r in results), 1)
            winner = next(r for r in results if not isinstance(r, Exception))
            with patch.object(store, "create_item", side_effect=OSError("alias save failed")):
                with self.assertRaises(OSError):
                    await complete(store, winner)
            with self.assertRaises(AdmissionRejected):
                await acquire(store, conversation_id="conv-test", previous_response_id=None, response_id="next")
