"""Low-cost tests for the local fixture/tool adapter; no model or Azure calls."""

import asyncio
import json
import unittest

from agent_framework import AgentSession, FunctionInvocationContext

from reasonfuse.local_runtime import LocalOperationsServer, build_local_tools, reset_operations_fixture
from reasonfuse.validation.middleware import ValidationMiddleware


class LocalRuntimeTests(unittest.TestCase):
    def test_tools_use_the_existing_http_fixture(self):
        with LocalOperationsServer() as operations:
            tools = build_local_tools(operations.base_url)
            result = asyncio.run(tools["operations___dns_resolution"].invoke(
                arguments={"hostname": "api.reasonfuse.local"}
            ))
            body = json.loads(result[0].text)
            self.assertEqual(body["status"], "RESOLVED")
            self.assertEqual(tools["operations___restart_service"].approval_mode, "always_require")

    def test_restart_tool_keeps_acceptance_separate_from_fresh_status(self):
        with LocalOperationsServer() as operations:
            reset_operations_fixture(operations.base_url, mode="verified")
            tools = build_local_tools(operations.base_url)
            accepted = asyncio.run(tools["operations___restart_service"].invoke(
                arguments={"service_name": "orders"}
            ))
            accepted_body = json.loads(accepted[0].text)
            self.assertTrue(accepted_body["accepted"])
            status = asyncio.run(tools["operations___service_status"].invoke(
                arguments={"service_name": "orders"}
            ))
            status_body = json.loads(status[0].text)
            self.assertEqual(status_body["service_health"], "HEALTHY")
            self.assertEqual(status_body["generation"], accepted_body["generation"])

    def test_validation_middleware_blocks_the_local_tool_before_http(self):
        with LocalOperationsServer() as operations:
            tools = build_local_tools(operations.base_url)
            session = AgentSession()
            context = FunctionInvocationContext(
                tools["operations___dns_resolution"],
                {"hostname": "blocked.reasonfuse.local"},
                session=session,
            )
            called = False

            async def call_next():
                nonlocal called
                called = True

            asyncio.run(ValidationMiddleware().process(context, call_next))
            self.assertFalse(called)
            self.assertEqual(context.result["status"], "BLOCKED")
