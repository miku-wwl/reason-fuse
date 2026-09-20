"""P0 policy, observation, inventory and persistence regressions; no network."""

import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
import yaml
from agent_framework import AgentSession, Content, FunctionInvocationContext, tool

from p0_support import ScriptedClient, UNSUPPORTED_SUCCESS, approval_message, call, make_agent
from reasonfuse.config import runtime_configuration
from reasonfuse.core.contract import RunContract
from reasonfuse.core.engine import ReasonFuseEngine, SIDE_EFFECT_TO_RESOURCE
from reasonfuse.core.middleware import ReasonFuseFunctionMiddleware, _core_tool_name
from reasonfuse.core.outcome import OutcomeVerifier, PostconditionRegistry
from reasonfuse.core.provider import CoreStateProvider
from reasonfuse.core.state import ReasonFuseState
from reasonfuse.local_runtime import build_local_agent, build_local_tools

CORE = "reasonfuse_core_v1"
ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_missing_configuration_defaults_to_enabled_runtime(self):
        config = runtime_configuration()
        self.assertEqual(config.profile, "runtime")
        self.assertTrue(config.enabled)
        self.assertTrue(config.contract.require_postcondition_for_side_effects)

    def test_invalid_configuration_rejected_at_construction(self):
        cases = [
            {"REASONFUSE_ENABLED": "yes"}, {"REASONFUSE_PROFILE": "test-typo"},
            {"REASONFUSE_CONTRACT_JSON": "{"}, {"REASONFUSE_CONTRACT_JSON": "[]"},
            {"REASONFUSE_CONTRACT_JSON": '{"max_steps":0}'},
            {"REASONFUSE_CONTRACT_JSON": '{"max_tool_calls":true}'},
            {"REASONFUSE_CONTRACT_JSON": '{"unknown_field":1}'},
            {"REASONFUSE_CONTRACT_JSON": '{"require_postcondition_for_side_effects":"false"}'},
        ]
        for values in cases:
            with self.subTest(values=values), patch.dict(os.environ, values, clear=True):
                with self.assertRaises((ValueError, TypeError)):
                    CoreStateProvider()

    def test_runtime_cannot_disable_policy_or_postconditions(self):
        for values in [{"REASONFUSE_ENABLED": "false"}, {
            "REASONFUSE_CONTRACT_JSON": '{"require_postcondition_for_side_effects":false}',
        }]:
            with self.subTest(values=values), patch.dict(os.environ, values):
                with self.assertRaises(ValueError):
                    runtime_configuration()

    def test_invalid_startup_precedes_both_client_constructors(self):
        from reasonfuse.agent import build_agent
        with patch.dict(os.environ, {"REASONFUSE_ENABLED": "invalid"}), \
                patch("reasonfuse.agent.FoundryChatClient") as hosted, \
                patch("reasonfuse.agent.DefaultAzureCredential") as credentials, \
                patch("reasonfuse.local_runtime.FoundryLocalClient") as local:
            with self.assertRaises(ValueError):
                build_agent()
            with self.assertRaises(ValueError):
                build_local_agent("http://fixture.invalid")
            hosted.assert_not_called()
            credentials.assert_not_called()
            local.assert_not_called()

    def test_explicit_evaluation_off(self):
        with patch.dict(os.environ, {"REASONFUSE_PROFILE": "evaluation", "REASONFUSE_ENABLED": "false"}):
            self.assertFalse(runtime_configuration().enabled)


class ObservationTests(unittest.TestCase):
    def pending_engine(self):
        engine = ReasonFuseEngine(contract=RunContract(max_stalled_steps=20,
                                                       required_objective_progress_interval=20))
        engine.record("restart_service", {"service_name": "orders"},
                      {"accepted": True, "generation": "g2"}, executed=True, side_effect=True)
        return engine

    def test_only_registered_verifier_and_resource_consume_obligation(self):
        for tool_name, resource in [("database_health", "orders"), ("service_status", "payments")]:
            with self.subTest(tool=tool_name, resource=resource):
                engine = self.pending_engine()
                args = {"service_name": resource}
                self.assertTrue(engine.before_dispatch(tool_name, args).allow)
                result = engine.record(tool_name, args, {"resource": resource, "generation": "g2",
                                                        "service_health": "HEALTHY"}, executed=True)
                self.assertFalse(result.signals["useful_recheck"])
                self.assertFalse(engine.state.pending_postcondition["consumed"])
                self.assertTrue(engine.state.verification_reserve_available)
                self.assertTrue(engine.pending_verification("service_status", {"service_name": "orders"}))
                engine.record("service_status", {"service_name": "orders"}, {}, executed=True)
                self.assertTrue(engine.state.pending_postcondition["consumed"])
                self.assertFalse(engine.state.verification_reserve_available)

    def test_freshness_resource_and_output_contract(self):
        accepted = {"accepted": True, "generation": "g2", "resource": "orders"}
        good = {"resource": "orders", "generation": "g2", "service_health": "HEALTHY"}
        cases = [
            (accepted, good, "OUTCOME_VERIFIED"),
            (accepted, {**good, "service_health": "UNHEALTHY"}, "POSTCONDITION_FAILED"),
            (accepted, {**good, "service_health": "DEGRADED"}, "POSTCONDITION_FAILED"),
            (accepted, {**good, "generation": "g1"}, "OUTCOME_UNKNOWN"),
            (accepted, {k: v for k, v in good.items() if k != "generation"}, "OUTCOME_UNKNOWN"),
            (accepted, {**good, "resource": "payments"}, "OUTCOME_UNKNOWN"),
            ({**accepted, "resource": "payments"}, good, "OUTCOME_UNKNOWN"),
            (accepted, {**good, "service_health": True}, "OUTCOME_UNKNOWN"),
            (accepted, {**good, "status": "stale"}, "OUTCOME_UNKNOWN"),
            (accepted, None, "OUTCOME_UNKNOWN"), (accepted, "healthy", "OUTCOME_UNKNOWN"),
        ]
        for missing in (None, "", " ", 2):
            cases.append(({**accepted, "generation": missing}, {**good, "generation": missing}, "OUTCOME_UNKNOWN"))
        for action, observed, outcome in cases:
            with self.subTest(action=action, observed=observed):
                self.assertEqual(OutcomeVerifier().verify("restart_service", action, observed,
                                                         requested_resource="orders")["outcome"], outcome)

    def observe(self, engine, name, fields):
        return engine.record(name, {"service_name": "orders"}, {
            "world_state": {"service_name": "orders", **fields},
        }, executed=True).signals["world_state_delta"]

    def test_alternating_unchanged_partial_views_do_not_manufacture_progress(self):
        engine = ReasonFuseEngine()
        service = {"service_health": "HEALTHY", "generation": "g1"}
        database = {"database_state": "HEALTHY"}
        changes = [self.observe(engine, name, fields) for _ in range(4)
                   for name, fields in [("service_status", service), ("database_health", database)]]
        self.assertEqual(changes, [True, True, False, False, False, False, False, False])
        self.assertEqual(engine.state.world_state_snapshot["orders"], {
            "service_name": "orders", **service, **database,
        })

    def test_real_field_changes_and_new_fields_are_progress_once(self):
        for name, field, old, new in [
            ("service_status", "service_health", "HEALTHY", "DEGRADED"),
            ("database_health", "database_state", "HEALTHY", "UNHEALTHY"),
            ("service_status", "generation", "g1", "g2"),
            ("service_status", "replica_count", None, 3),
        ]:
            with self.subTest(field=field):
                engine = ReasonFuseEngine()
                self.observe(engine, name, {} if old is None else {field: old})
                self.assertTrue(self.observe(engine, name, {field: new}))
                self.assertFalse(self.observe(engine, name, {field: new}))

    def test_world_merge_survives_serialization(self):
        engine = ReasonFuseEngine()
        self.observe(engine, "service_status", {"service_health": "HEALTHY", "generation": "g1"})
        self.observe(engine, "database_health", {"database_state": "HEALTHY"})
        restored = ReasonFuseEngine(ReasonFuseState.from_dict(json.loads(json.dumps(engine.state.to_dict()))))
        self.assertFalse(self.observe(restored, "service_status", {"service_health": "HEALTHY", "generation": "g1"}))

    def test_state_snapshots_do_not_alias_live_obligation(self):
        engine = self.pending_engine()
        snapshot = engine.state.to_dict()
        snapshot["pending_postcondition"]["accepted_result"]["generation"] = "tampered"
        self.assertEqual(engine.state.pending_postcondition["accepted_result"]["generation"], "g2")
        restored = ReasonFuseState.from_dict(snapshot)
        restored.pending_postcondition["resource"] = "payments"
        self.assertEqual(snapshot["pending_postcondition"]["resource"], "orders")


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "REASONFUSE_PROFILE": "runtime", "REASONFUSE_ENABLED": "true", "REASONFUSE_CONTRACT_JSON": "{}",
            "TOOLBOX_ENDPOINT": "", "TOOLBOX_NAME": "", "FOUNDRY_IQ_MCP_ENDPOINT": "",
            "FOUNDRY_PROJECT_ENDPOINT": "https://local-test.invalid", "AZURE_AI_MODEL_DEPLOYMENT_NAME": "scripted",
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    async def test_disabled_session_rejected_by_runtime_and_preserved_in_evaluation(self):
        state = ReasonFuseState(reasonfuse_enabled=False).to_dict()
        session = AgentSession()
        with self.assertRaisesRegex(ValueError, "disabled session"):
            await CoreStateProvider().before_run(agent=None, session=session, context=None, state=state)
        self.assertFalse(state["reasonfuse_enabled"])
        with patch.dict(os.environ, {"REASONFUSE_PROFILE": "evaluation"}):
            await CoreStateProvider().before_run(agent=None, session=session, context=None, state=state)
        self.assertFalse(state["reasonfuse_enabled"])

    async def test_evaluation_postconditions_disabled_never_creates_partial_pending(self):
        with patch.dict(os.environ, {"REASONFUSE_PROFILE": "evaluation", "REASONFUSE_CONTRACT_JSON":
                                   '{"require_postcondition_for_side_effects":false}'}):
            session = AgentSession()
            state = session.state.setdefault(CORE, {})
            await CoreStateProvider().before_run(agent=None, session=session, context=None, state=state)
            middleware = ReasonFuseFunctionMiddleware()
            for name, result in [("restart_service", {"accepted": True, "generation": "g2"}),
                                 ("service_status", {"resource": "orders", "generation": "g2", "service_health": "HEALTHY"})]:
                @tool(name=name)
                def operation(service_name: str) -> str:
                    return "unused"
                context = FunctionInvocationContext(operation, {"service_name": "orders"}, session=session)
                async def invoke():
                    context.result = result
                # Two non-progress observations may legitimately trip containment.
                from agent_framework import MiddlewareTermination
                try:
                    await middleware.process(context, invoke)
                except MiddlewareTermination:
                    pass
                self.assertIsNone(state["pending_postcondition"])
                ReasonFuseState.from_dict(json.loads(json.dumps(state)))

    async def test_diagnostics_reports_live_enabled_profile_and_contract(self):
        agent, _ = make_agent([[call("diagnostics", "read_reasonfuse_state")], [Content.from_text("Read.")]], [])
        session = AgentSession()
        response = await agent.run("Read policy.", session=session)
        results = [c.result for m in response.messages for c in m.contents if c.type == "function_result"]
        payload = json.loads(results[0])
        self.assertTrue(payload["reasonfuse_enabled"])
        self.assertEqual(payload["runtime_profile"], "runtime")
        self.assertEqual(payload["contract_limits"], RunContract().to_dict())

    async def test_cloud_inventory_excludes_reset_and_fixture_reset_still_works(self):
        spec = importlib.util.spec_from_file_location("p0_cloud_fixture", ROOT / "cloud/operations-mcp/server.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        inventory = {item.name for item in await module.mcp.list_tools()}
        self.assertEqual(inventory, {"operations___service_status", "operations___restart_service"})
        for name in inventory - {"operations___service_status"}:
            self.assertIn(_core_tool_name(name), SIDE_EFFECT_TO_RESOURCE)
            PostconditionRegistry().get(_core_tool_name(name))
        module.state.restart_service("orders")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=module.app), base_url="http://localhost") as client:
            response = await client.post("/test/reset", json={"mode": "failed"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["restart_count"], 0)
            self.assertEqual(response.json()["mode"], "failed")
            self.assertEqual((await client.post("/test/reset", json={"mode": "bad"})).status_code, 400)
        self.assertTrue(module.state.restart_service("orders")["accepted"])

    async def test_local_inventory_has_only_registered_external_mutations(self):
        tools = build_local_tools("http://fixture.invalid")
        reads = {"dns_resolution", "database_health", "service_status", "retrieval_fixture"}
        self.assertEqual({_core_tool_name(name) for name in tools}, reads | set(SIDE_EFFECT_TO_RESOURCE))
        for name, item in tools.items():
            self.assertEqual(item.approval_mode, "never_require" if _core_tool_name(name) in reads else "always_require")

    async def test_hosted_allowlist_and_manifest_approval_match_inventory(self):
        from reasonfuse.agent import build_agent
        with patch.dict(os.environ, {"TOOLBOX_NAME": "operations-tools"}), \
                patch("reasonfuse.agent.FoundryToolbox", return_value=[]) as toolbox, \
                patch("reasonfuse.agent.Agent"), patch("reasonfuse.agent.FoundryChatClient"), \
                patch("reasonfuse.agent.DefaultAzureCredential"):
            build_agent()
        options = toolbox.call_args.kwargs
        self.assertEqual({_core_tool_name(name) for name in options["allowed_tools"]},
                         {"restart_service", "service_status"})
        self.assertEqual({_core_tool_name(name) for name in options["approval_mode"]["always_require_approval"]},
                         set(SIDE_EFFECT_TO_RESOURCE))
        manifest = yaml.safe_load((ROOT / "azure.yaml").read_text(encoding="utf-8"))
        approval = manifest["services"]["operations-tools"]["tools"][0]["require_approval"]
        self.assertEqual(approval, {"never": ["operations___service_status"], "always": ["operations___restart_service"]})
        self.assertEqual(manifest["services"]["reasonfuse"]["env"]["REASONFUSE_ENABLED"], "true")

    async def test_local_adapter_uses_shared_completion_and_core(self):
        client = ScriptedClient([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)]])
        with patch("reasonfuse.local_runtime.FoundryLocalClient", return_value=client):
            bundle = build_local_agent("http://fixture.invalid", bootstrap=False, prepare_model=False)
        session = AgentSession()
        with patch("reasonfuse.local_runtime._post", return_value='{"accepted":true,"generation":"g2"}') as restart, \
                patch("reasonfuse.local_runtime._get", return_value='{"resource":"orders","generation":"g2","service_health":"HEALTHY"}') as status:
            pending = await bundle.agent.run("Restart orders.", session=session)
            response = await bundle.agent.run(approval_message(pending), session=session)
        restart.assert_called_once()
        status.assert_called_once()
        self.assertIn("OUTCOME_VERIFIED", response.text)
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(session.to_dict()))

    async def test_hosted_server_history_configuration_accepts_completion_guard(self):
        from agent_framework_foundry_hosting import ResponsesHostServer
        tools = build_local_tools("http://fixture.invalid")
        agent, _ = make_agent([[call()], [Content.from_text(UNSUPPORTED_SUCCESS)]], tools.values())
        host = ResponsesHostServer(agent, history_source="agent_server")
        self.assertIs(host._agent, agent)
        self.assertFalse(agent.require_per_service_call_history_persistence)
        session = AgentSession()
        with patch("reasonfuse.local_runtime._post", return_value='{"accepted":true,"generation":"g2"}'), \
                patch("reasonfuse.local_runtime._get", return_value='{"resource":"orders","generation":"g2","service_health":"HEALTHY"}'):
            pending = await agent.run("Restart orders.", session=session)
            stream = agent.run(approval_message(pending), session=session, stream=True)
            updates = [update async for update in stream]
            final = await stream.get_final_response()
        self.assertIn("OUTCOME_VERIFIED", final.text)
        self.assertNotIn(UNSUPPORTED_SUCCESS, "".join(update.text for update in updates))
        self.assertNotIn(UNSUPPORTED_SUCCESS, json.dumps(session.to_dict()))
