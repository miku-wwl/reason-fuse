"""Adversarial lifecycle and response regressions against the pinned framework."""

import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agent_framework import AgentSession, Content, FunctionInvocationContext, Message, MiddlewareTermination, tool

from p0_support import UNSUPPORTED_SUCCESS, approval_message, approvals, call, make_agent
from reasonfuse.core.contract import RunContract
from reasonfuse.core.middleware import ReasonFuseFunctionMiddleware
from reasonfuse.core.provider import CoreStateProvider
from reasonfuse.core.state import ReasonFuseState

CORE = "reasonfuse_core_v1"


class RuntimeP0Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.environment = patch.dict("os.environ", {
            "REASONFUSE_PROFILE": "runtime", "REASONFUSE_ENABLED": "true",
            "REASONFUSE_CONTRACT_JSON": "{}", "TOOLBOX_ENDPOINT": "", "TOOLBOX_NAME": "",
            "FOUNDRY_IQ_MCP_ENDPOINT": "", "FOUNDRY_PROJECT_ENDPOINT": "https://local-test.invalid",
            "AZURE_AI_MODEL_DEPLOYMENT_NAME": "scripted",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.effects = 0
        self.reads = 0

    def tools(self, observation=None, before_read=None):
        @tool(name="operations___restart_service", approval_mode="always_require")
        async def restart(service_name: str) -> str:
            await asyncio.sleep(0)
            self.effects += 1  # No backend duplicate rejection.
            return json.dumps({"accepted": True, "generation": "g2", "status_code": 202})

        @tool(name="operations___service_status", approval_mode="never_require")
        async def status(service_name: str) -> str:
            self.reads += 1
            if before_read:
                await before_read()
            return json.dumps(observation if observation is not None else {
                "resource": service_name, "service_health": "HEALTHY", "generation": "g2",
            })
        return restart, status

    async def exercise(self, *, stream=False, approved=True, observation=None, tools_override=None):
        agent, client = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)]],
                                   tools_override or self.tools(observation))
        session = AgentSession()
        pending = await agent.run("Restart orders.", session=session)
        self.assertEqual(len(approvals(pending)), 1)
        self.assertEqual(self.effects, 0)
        self.assertEqual(session.state[CORE]["side_effect_count"], 0)
        if stream:
            response_stream = agent.run(approval_message(pending, approved), session=session, stream=True)
            updates = [update async for update in response_stream]
            final = await response_stream.get_final_response()
            self.assertNotIn(UNSUPPORTED_SUCCESS, "".join(u.text for u in updates))
        else:
            final = await agent.run(approval_message(pending, approved), session=session)
        self.assertNotIn(UNSUPPORTED_SUCCESS, final.text)
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(session.to_dict()))
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(final.to_dict()))
        return session, final, client

    async def test_skipped_verifier_nonstreaming_is_completed_by_runtime(self):
        session, final, client = await self.exercise()
        self.assertEqual((self.effects, self.reads), (1, 1))
        self.assertEqual(session.state[CORE]["action_lifecycle"]["status"], "VERIFIED")
        self.assertEqual(session.state[CORE]["tool_call_count"], 2)
        self.assertIsNone(session.state[CORE]["pending_postcondition"])
        self.assertIn("OUTCOME_VERIFIED", final.text)
        self.assertEqual(len(client.requests), 2)  # Completion adds no model call.

    async def test_skipped_verifier_streaming_is_completed_by_runtime(self):
        session, final, _ = await self.exercise(stream=True)
        self.assertEqual(self.reads, 1)
        self.assertIn("OUTCOME_VERIFIED", final.text)
        self.assertFalse(session.state[CORE]["contained"])

    async def test_stream_releases_nothing_until_verification_finishes(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def before_read():
            entered.set()
            await release.wait()
        agent, _ = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)]], self.tools(before_read=before_read))
        session = AgentSession()
        pending = await agent.run("Restart.", session=session)
        response_stream = agent.run(approval_message(pending), session=session, stream=True)
        first = asyncio.create_task(response_stream.__anext__())
        await asyncio.wait_for(entered.wait(), 2)
        self.assertFalse(first.done(), "A chunk escaped before the runtime verdict")
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(session.to_dict()))
        release.set()
        update = await first
        remaining = [item async for item in response_stream]
        self.assertNotIn(UNSUPPORTED_SUCCESS, "".join(item.text for item in [update, *remaining]))

    async def test_denial_nonstreaming_replaces_fabricated_success(self):
        session, final, _ = await self.exercise(approved=False)
        self.assertEqual((self.effects, self.reads), (0, 0))
        self.assertEqual(session.state[CORE]["denied_proposal_count"], 1)
        self.assertEqual(json.loads(final.text)["outcome"], "DENIED")

    async def test_denial_streaming_replaces_fabricated_success(self):
        session, final, _ = await self.exercise(approved=False, stream=True)
        self.assertEqual((self.effects, self.reads), (0, 0))
        self.assertEqual(json.loads(final.text)["outcome"], "DENIED")

    async def test_native_approval_occurrence_binding_is_preserved(self):
        agent, _ = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)],
                               [Content.from_text(UNSUPPORTED_SUCCESS)]], self.tools())
        session = AgentSession()
        pending = await agent.run("Restart.", session=session)
        forged = approvals(pending)[0].to_function_approval_response(approved=True)
        forged.id = "not-issued"
        result = await agent.run(Message("user", [forged]), session=session)
        self.assertEqual(self.effects, 0)
        self.assertNotIn(UNSUPPORTED_SUCCESS, result.text)
        approved = approval_message(pending)
        # Changing the embedded resource does not change the framework's stored authority.
        approved.contents[0].function_call.arguments = '{"service_name":"payments"}'
        result = await agent.run(approved, session=session)
        self.assertEqual(self.effects, 1)
        self.assertEqual(session.state[CORE]["action_lifecycle"]["resource"], "orders")

    async def test_concurrent_approved_calls_execute_only_one_lifecycle(self):
        agent, _ = make_agent([[call("a"), call("b")]], self.tools())
        session = AgentSession()
        pending = await agent.run("Restart twice.", session=session)
        self.assertEqual(len(approvals(pending)), 2)
        self.assertEqual(self.effects, 0)
        result = await agent.run(approval_message(pending), session=session)
        core = session.state[CORE]
        self.assertEqual(self.effects, 1)
        self.assertEqual(self.reads, 1)
        self.assertEqual(core["side_effect_count"], 1)
        self.assertEqual(core["tool_call_count"], 2)
        self.assertEqual(core["last_postcondition_result"]["outcome"], "OUTCOME_VERIFIED")
        self.assertEqual(core["last_proposal"]["status"], "BLOCKED")
        self.assertNotIn(UNSUPPORTED_SUCCESS, result.text)

    async def test_concurrent_dispatch_retains_obligation_before_completion(self):
        session = AgentSession()
        session.state[CORE] = ReasonFuseState().to_dict()
        middleware = ReasonFuseFunctionMiddleware()
        contexts = [FunctionInvocationContext(SimpleNamespace(name="operations___restart_service"),
                                             {"service_name": "orders"}, session=session) for _ in range(2)]
        async def dispatch(context):
            async def next_call():
                await asyncio.sleep(0)
                self.effects += 1
                context.result = {"accepted": True, "generation": "g2"}
            try:
                await middleware.process(context, next_call)
            except MiddlewareTermination:
                pass
        await asyncio.gather(*(dispatch(context) for context in contexts))
        core = session.state[CORE]
        self.assertEqual((self.effects, core["tool_call_count"], core["side_effect_count"]), (1, 1, 1))
        self.assertEqual(core["pending_postcondition"]["generation"], "g2")
        self.assertTrue(core["verification_reserve_available"])

    async def test_cancel_after_mutation_keeps_attempt_and_blocks_replay(self):
        entered = asyncio.Event()
        session = AgentSession()
        session.state[CORE] = ReasonFuseState().to_dict()
        middleware = ReasonFuseFunctionMiddleware()
        context = FunctionInvocationContext(SimpleNamespace(name="restart_service"), {"service_name": "orders"}, session=session)
        async def execute():
            self.effects += 1
            entered.set()
            await asyncio.Event().wait()
        task = asyncio.create_task(middleware.process(context, execute))
        await entered.wait()
        self.assertEqual(session.state[CORE]["action_lifecycle"]["status"], "DISPATCHING")
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(session.state[CORE]["side_effect_count"], 1)
        self.assertEqual(session.state[CORE]["action_lifecycle"]["status"], "UNKNOWN")
        self.assertTrue(session.state[CORE]["contained"])
        with self.assertRaises(MiddlewareTermination):
            await middleware.process(context, execute)
        self.assertEqual(self.effects, 1)
        restored = AgentSession.from_dict(json.loads(json.dumps(session.to_dict())))
        self.assertTrue(restored.state[CORE]["contained"])

    async def test_restored_dispatching_is_unknown_not_replayable(self):
        state = ReasonFuseState(side_effect_count=1, tool_call_count=1, action_lifecycle={
            "status": "DISPATCHING", "action": "restart_service", "resource": "orders",
        }).to_dict()
        session = AgentSession()
        await CoreStateProvider().before_run(agent=None, session=session, context=None, state=state)
        self.assertTrue(state["contained"])
        self.assertEqual(state["action_lifecycle"]["status"], "UNKNOWN")

    async def test_failed_postcondition_is_runtime_result_and_contains(self):
        session, final, _ = await self.exercise(observation={
            "resource": "orders", "generation": "g2", "service_health": "UNHEALTHY",
        })
        self.assertIn("POSTCONDITION_FAILED", final.text)
        self.assertTrue(session.state[CORE]["contained"])

    async def test_stale_postcondition_is_unknown_and_contains(self):
        session, final, _ = await self.exercise(stream=True, observation={
            "resource": "orders", "generation": "g1", "service_health": "HEALTHY",
        })
        self.assertIn("OUTCOME_UNKNOWN", final.text)
        self.assertTrue(session.state[CORE]["contained"])

    async def test_missing_verifier_is_unknown_without_extra_model_call(self):
        restart, _ = self.tools()
        session, final, client = await self.exercise(tools_override=[restart])
        self.assertEqual(self.reads, 0)
        self.assertIn("registered_verifier_unavailable", final.text)
        self.assertTrue(session.state[CORE]["contained"])
        self.assertEqual(len(client.requests), 2)

    async def test_verifier_timeout_fails_closed(self):
        async def hang():
            await asyncio.Event().wait()
        with patch("reasonfuse.completion.VERIFICATION_TIMEOUT_SECONDS", 0.01):
            session, final, _ = await self.exercise(tools_override=self.tools(before_read=hang))
        self.assertEqual(self.effects, 1)
        self.assertTrue(session.state[CORE]["contained"])
        self.assertIn("OUTCOME_UNKNOWN", final.text)

    async def test_verification_uses_last_reserved_budget_slot(self):
        with patch.dict("os.environ", {"REASONFUSE_CONTRACT_JSON": '{"max_steps":2,"max_tool_calls":2}'}):
            session, final, _ = await self.exercise()
        self.assertEqual(session.state[CORE]["tool_call_count"], 2)
        self.assertIn("OUTCOME_VERIFIED", final.text)

    async def test_native_approval_continues_after_session_serialization(self):
        agent, _ = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)]], self.tools())
        session = AgentSession()
        pending = await agent.run("Restart.", session=session)
        restored = AgentSession.from_dict(json.loads(json.dumps(session.to_dict())))
        result = await agent.run(approval_message(pending), session=restored)
        self.assertEqual(self.effects, 1)
        self.assertIn("OUTCOME_VERIFIED", result.text)

    async def test_normal_text_without_action_is_preserved(self):
        agent, _ = make_agent([[Content.from_text("Hello.")]], [])
        session = AgentSession()
        result = await agent.run("Hello", session=session)
        self.assertEqual(result.text, "Hello.")

    async def test_explicit_evaluation_off_is_available(self):
        with patch.dict("os.environ", {"REASONFUSE_PROFILE": "evaluation", "REASONFUSE_ENABLED": "false"}):
            agent, _ = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)]], self.tools())
            session = AgentSession()
            pending = await agent.run("Restart", session=session)
            result = await agent.run(approval_message(pending), session=session)
        self.assertEqual(self.effects, 1)
        self.assertEqual(self.reads, 0)
        self.assertIn(UNSUPPORTED_SUCCESS, result.text)
        self.assertFalse(session.state[CORE]["reasonfuse_enabled"])

    async def test_model_supplied_registered_verifier_is_not_repeated(self):
        agent, _ = make_agent([[call()], [call("read", "operations___service_status")],
                               [Content.from_text(UNSUPPORTED_SUCCESS)]], self.tools())
        session = AgentSession()
        pending = await agent.run("Restart.", session=session)
        result = await agent.run(approval_message(pending), session=session)
        self.assertEqual((self.effects, self.reads), (1, 1))
        self.assertIn("OUTCOME_VERIFIED", result.text)
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(session.to_dict()))

    async def test_missing_freshness_and_malformed_outputs_are_unknown(self):
        for observation in [
            {"resource": "orders", "service_health": "HEALTHY"},
            {"resource": "payments", "service_health": "HEALTHY", "generation": "g2"},
            {"resource": "orders", "service_health": "made-up", "generation": "g2"},
        ]:
            with self.subTest(observation=observation):
                self.effects = self.reads = 0
                session, result, _ = await self.exercise(observation=observation)
                self.assertIn("OUTCOME_UNKNOWN", result.text)
                self.assertTrue(session.state[CORE]["contained"])
                self.assertEqual((self.effects, self.reads), (1, 1))

    async def test_verifier_requiring_approval_is_not_automatically_executed(self):
        restart, status = self.tools()
        status.approval_mode = "always_require"
        session, result, _ = await self.exercise(tools_override=[restart, status])
        self.assertEqual(self.reads, 0)
        self.assertIn("OUTCOME_UNKNOWN", result.text)
        self.assertTrue(session.state[CORE]["contained"])

    async def test_auto_verifier_must_match_original_namespace(self):
        restart, status = self.tools()
        status.name = "another-server___service_status"
        session, result, _ = await self.exercise(tools_override=[restart, status])
        self.assertEqual(self.reads, 0)
        self.assertIn("OUTCOME_UNKNOWN", result.text)
        self.assertTrue(session.state[CORE]["contained"])

    async def test_stream_failure_after_acceptance_keeps_unknown_and_no_history_claim(self):
        agent, _ = make_agent([[call()], RuntimeError("scripted stream interruption")], self.tools())
        session = AgentSession()
        pending = await agent.run("Restart.", session=session)
        exposed = []
        with self.assertRaisesRegex(RuntimeError, "stream interruption"):
            async for update in agent.run(approval_message(pending), session=session, stream=True):
                exposed.append(update)
        self.assertEqual(exposed, [])
        self.assertEqual(self.effects, 1)
        self.assertEqual(session.state[CORE]["action_lifecycle"]["status"], "UNKNOWN")
        self.assertTrue(session.state[CORE]["contained"])
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(session.to_dict()))

    async def test_accounting_exception_after_mutation_contains_reserved_action(self):
        session = AgentSession()
        session.state[CORE] = ReasonFuseState().to_dict()
        context = FunctionInvocationContext(SimpleNamespace(name="restart_service"),
                                            {"service_name": "orders"}, session=session)
        async def execute():
            self.effects += 1
            context.result = {"accepted": True, "generation": "g2"}
        with patch("reasonfuse.core.engine.ReasonFuseEngine.record", side_effect=ValueError("broken accounting")):
            with self.assertRaisesRegex(ValueError, "broken accounting"):
                await ReasonFuseFunctionMiddleware().process(context, execute)
        self.assertEqual(self.effects, 1)
        self.assertEqual(session.state[CORE]["side_effect_count"], 1)
        self.assertEqual(session.state[CORE]["action_lifecycle"]["status"], "UNKNOWN")
        self.assertTrue(session.state[CORE]["contained"])

    async def test_unknown_lifecycle_cannot_replay_with_new_native_approval(self):
        restart, _ = self.tools()
        agent, _ = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)], [call("retry")]], [restart])
        session = AgentSession()
        pending = await agent.run("Restart.", session=session)
        await agent.run(approval_message(pending), session=session)
        self.assertEqual(session.state[CORE]["action_lifecycle"]["status"], "UNKNOWN")
        restored = AgentSession.from_dict(json.loads(json.dumps(session.to_dict())))
        retry = await agent.run("Retry restart.", session=restored)
        result = await agent.run(approval_message(retry), session=restored)
        self.assertEqual(self.effects, 1)
        self.assertEqual(restored.state[CORE]["side_effect_count"], 1)
        self.assertTrue(restored.state[CORE]["contained"])
        self.assertIn("OUTCOME_UNKNOWN", result.text)
        self.assertNotIn(UNSUPPORTED_SUCCESS, result.text)

    async def test_two_concurrent_approval_turns_share_one_session_authority(self):
        agent, _ = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)],
                               [Content.from_text(UNSUPPORTED_SUCCESS)]], self.tools())
        session = AgentSession()
        pending = await agent.run("Restart.", session=session)
        responses = await asyncio.gather(*[
            agent.run(approval_message(pending), session=session) for _ in range(2)
        ])
        self.assertEqual((self.effects, self.reads), (1, 1))
        self.assertEqual(session.state[CORE]["side_effect_count"], 1)
        for response in responses:
            self.assertNotIn(UNSUPPORTED_SUCCESS, response.text)

    async def test_concurrent_ordinary_reads_do_not_lose_accounting(self):
        session = AgentSession()
        session.state[CORE] = ReasonFuseState().to_dict()
        async def read(index):
            context = FunctionInvocationContext(SimpleNamespace(name="service_status"),
                                                {"service_name": f"service-{index}"}, session=session)
            async def execute():
                await asyncio.sleep(0)
                context.result = {"world_state": {"service_name": f"service-{index}", "generation": "g1"}}
            await ReasonFuseFunctionMiddleware().process(context, execute)
        await asyncio.gather(*(read(index) for index in range(5)))
        self.assertEqual(session.state[CORE]["tool_call_count"], 5)
        self.assertEqual(len(session.state[CORE]["world_state_snapshot"]), 5)

    async def test_per_call_history_persistence_rejected_before_execution(self):
        agent, client = make_agent([[call()]], self.tools())
        agent.require_per_service_call_history_persistence = True
        with self.assertRaisesRegex(ValueError, "run-end history"):
            await agent.run("Restart.", session=AgentSession())
        self.assertEqual(client.requests, [])
        self.assertEqual(self.effects, 0)

    async def test_cached_structured_model_answer_cannot_escape_completion(self):
        from agent_framework import AgentResponse
        from reasonfuse.completion import ReasonFuseCompletionMiddleware
        from reasonfuse.runtime import RuntimeTurn
        session = AgentSession()
        session.state[CORE] = ReasonFuseState(
            side_effect_count=1,
            action_lifecycle={"action": "restart_service", "resource": "orders", "status": "UNKNOWN"},
            last_postcondition_result={"outcome": "OUTCOME_UNKNOWN", "reason": "interrupted"},
            contained=True,
        ).to_dict()
        response = AgentResponse(
            messages=[Message("assistant", [Content.from_text(UNSUPPORTED_SUCCESS)],
                              raw_representation={"text": UNSUPPORTED_SUCCESS})],
            value={"result": UNSUPPORTED_SUCCESS}, raw_representation={"text": UNSUPPORTED_SUCCESS},
        )
        await ReasonFuseCompletionMiddleware()._complete(SimpleNamespace(session=session), RuntimeTurn(), [], response)
        self.assertEqual(response.value["outcome"], "OUTCOME_UNKNOWN")
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(response.value))
        self.assertIsNone(response.raw_representation)
