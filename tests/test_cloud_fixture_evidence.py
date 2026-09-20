"""Independent cloud fixture evidence must not alter operational semantics."""

import importlib.util
from pathlib import Path
import unittest

import httpx


class CloudFixtureEvidenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "cloud/operations-mcp/server.py"
        spec = importlib.util.spec_from_file_location("cloud_fixture_evidence", path)
        self.fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.fixture)

    async def test_snapshot_counts_attempts_independently_without_consuming_verification(self):
        state = self.fixture.state
        accepted = state.restart_service("orders")
        rejected = state.restart_service("orders")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.fixture.app), base_url="http://localhost") as client:
            snapshot = (await client.get("/test/state")).json()
        self.assertEqual(snapshot["restart_count"], 1)
        self.assertEqual(snapshot["restart_attempt_count"], 2)
        self.assertEqual(snapshot["status_read_count"], 0)
        self.assertTrue(snapshot["restart_pending"])
        self.assertTrue(accepted["accepted"])
        self.assertFalse(rejected["accepted"])
        self.assertEqual([event["result"]["status_code"] for event in snapshot["events"]], [202, 409])
        observed = state.service_status("orders")
        self.assertEqual(observed["generation"], accepted["generation"])
        self.assertEqual(state.snapshot()["status_read_count"], 1)
        self.assertEqual(state.snapshot()["events"][-1]["operation"], "service_status")

    async def test_evidence_routes_are_not_agent_tools_and_reset_clears_counters(self):
        names = {item.name for item in await self.fixture.mcp.list_tools()}
        self.assertEqual(names, {"operations___restart_service", "operations___service_status"})
        self.fixture.state.restart_service("orders")
        self.fixture.state.reset("unknown")
        snapshot = self.fixture.state.snapshot()
        self.assertEqual(snapshot["restart_count"], 0)
        self.assertEqual(snapshot["restart_attempt_count"], 0)
        self.assertEqual(snapshot["events"], [])
