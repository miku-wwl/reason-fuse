"""Construction gap regressions: budgets, resumed obligations and false progress."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agent_framework import AgentSession, FunctionInvocationContext, MiddlewareTermination, tool
from reasonfuse.core.contract import RunContract
from reasonfuse.core.engine import ReasonFuseEngine
from reasonfuse.core.middleware import ReasonFuseFunctionMiddleware
from reasonfuse.core.outcome import OutcomeVerifier
from reasonfuse.core.progress import result_signals
from reasonfuse.core.detectors import retrieval_churn
from reasonfuse.core.state import ReasonFuseState
from reasonfuse.core.provider import CoreStateProvider


class ConstructionBoundaryTests(unittest.TestCase):
    def test_off_exceeds_all_behavioral_budgets(self):
        engine = ReasonFuseEngine(ReasonFuseState(reasonfuse_enabled=False))
        for _ in range(15):
            self.assertTrue(engine.before_dispatch("dns_resolution", {}).allow)
            engine.record("dns_resolution", {}, {}, executed=True)
        self.assertFalse(engine.state.contained)

    def test_step_and_progress_interval_are_enforced(self):
        for limits in ({"max_steps": 2}, {"required_objective_progress_interval": 2}):
            contract = RunContract(max_stalled_steps=10, **limits)
            engine = ReasonFuseEngine(contract=contract)
            for i in range(2):
                self.assertTrue(engine.before_dispatch("dns_resolution", {"i": i}).allow)
                engine.record("dns_resolution", {"i": i}, {}, executed=True)
            self.assertFalse(engine.before_dispatch("dns_resolution", {"i": 3}).allow)

    def test_side_effect_budget_does_not_block_diagnostics(self):
        engine = ReasonFuseEngine(ReasonFuseState(side_effect_count=1))
        self.assertTrue(engine.before_dispatch("dns_resolution", {}).allow)
        self.assertFalse(engine.before_dispatch("restart_service", {}).allow)

    def test_invalid_contract_boolean_and_detector_window(self):
        for data in ({"max_steps": True}, {"max_oscillation_cycles": 1}, {"max_retrieval_churn": 1}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                RunContract(**data)

    def test_missing_observations_and_todo_are_not_objective_progress(self):
        previous = {"world_state": {"service_health": "HEALTHY"},
                    "retrieval": {"source_keys": ["A"]}}
        signals = result_signals(previous, {}, {"status": "OPEN"}, {"status": "COMPLETED"})
        self.assertTrue(signals.todo_delta)
        self.assertFalse(signals.objective_progress)

    def test_evidence_is_accumulated_across_tools(self):
        engine = ReasonFuseEngine()
        for evidence in (["A"], ["B"], ["A"]):
            observation = engine.record("diagnostic", {}, {"evidence_keys": evidence}, executed=True)
        self.assertFalse(observation.objective_progress)
        self.assertEqual(set(engine.state.evidence_keys), {"A", "B"})

    def test_retrieval_version_change_is_not_churn(self):
        attempts = [{"query": str(i), "source_keys": ["A"], "knowledge_base_version": str(i)}
                    for i in range(3)]
        self.assertFalse(retrieval_churn(attempts).tripped)

    def test_stale_healthy_and_missing_health_are_unknown(self):
        verifier = OutcomeVerifier()
        accepted = {"accepted": True, "generation": "g2"}
        for observation in (
            {"resource": "orders", "service_health": "HEALTHY", "status": "stale", "generation": "g2"},
            {"resource": "orders", "service_health": "HEALTHY", "generation": "g1"},
            {"resource": "orders", "generation": "g2"},
            {"resource": "orders", "generation": "g2", "service_health": []},
        ):
            self.assertEqual(verifier.verify("restart_service", accepted, observation,
                             requested_resource="orders")["outcome"], "OUTCOME_UNKNOWN")

    def test_resume_preserves_bound_recheck_and_acceptance_is_not_progress(self):
        engine = ReasonFuseEngine()
        observation = engine.record("restart_service", {"body": {"service_name": "orders"}},
                                    {"accepted": True, "generation": "g1", "world_state": {"health": "HEALTHY"}},
                                    executed=True, side_effect=True)
        self.assertFalse(observation.objective_progress)
        engine = ReasonFuseEngine(ReasonFuseState.from_dict(engine.state.to_dict()))
        self.assertTrue(engine.before_dispatch("service_status", {"service_name": "orders"}).allow)
        observation = engine.record("service_status", {"service_name": "orders"},
                                    {"resource": "orders", "generation": "g1", "service_health": "HEALTHY"},
                                    executed=True)
        self.assertTrue(observation.signals["useful_recheck"])

    def test_required_verification_is_reserved_inside_total_budget(self):
        engine = ReasonFuseEngine(contract=RunContract(max_tool_calls=1))
        self.assertFalse(engine.before_dispatch("restart_service", {"service_name": "orders"}).allow)

    def test_rejected_side_effect_creates_no_obligation(self):
        engine = ReasonFuseEngine()
        engine.record("restart_service", {"service_name": "orders"}, {"accepted": False},
                      executed=True, side_effect=True)
        self.assertIsNone(engine.state.pending_postcondition)

    def test_middleware_counts_failed_dispatch(self):
        async def scenario():
            session = AgentSession()
            session.state["reasonfuse_core_v1"] = ReasonFuseState().to_dict()

            @tool
            def dns_resolution() -> str:
                return "unused"

            context = FunctionInvocationContext(dns_resolution, {}, session=session)

            async def fail():
                raise TimeoutError("synthetic timeout")

            try:
                await ReasonFuseFunctionMiddleware().process(context, fail)
            except (TimeoutError, MiddlewareTermination):
                pass
            self.assertEqual(session.state["reasonfuse_core_v1"]["tool_call_count"], 1)
            self.assertEqual(session.state["reasonfuse_core_v1"]["failed_call_count"], 1)
        asyncio.run(scenario())

    def test_unrelated_read_does_not_consume_postcondition(self):
        engine = ReasonFuseEngine(contract=RunContract(max_stalled_steps=10, required_objective_progress_interval=10))
        engine.record("restart_service", {"service_name": "orders"}, {"accepted": True, "generation": "g1"},
                      executed=True, side_effect=True)
        result = engine.record("service_status", {"service_name": "payments"},
                               {"resource": "payments", "generation": "g1"}, executed=True)
        self.assertFalse(result.signals["useful_recheck"])
        self.assertFalse(engine.state.pending_postcondition["consumed"])

    def test_database_health_alias_preserves_useful_recheck(self):
        engine = ReasonFuseEngine()
        engine.record("restart_service", {"service_name": "orders"}, {"accepted": True, "generation": "g1"},
                      executed=True, side_effect=True)
        engine = ReasonFuseEngine(ReasonFuseState.from_dict(engine.state.to_dict()))
        self.assertTrue(engine.before_dispatch("database_health", {"service_name": "orders"}).allow)
        result = engine.record("database_health", {"service_name": "orders"},
                               {"resource": "orders", "generation": "g1"}, executed=True)
        self.assertTrue(result.signals["useful_recheck"])

    def test_optional_postcondition_configuration_is_honored(self):
        engine = ReasonFuseEngine(contract=RunContract(require_postcondition_for_side_effects=False))
        engine.record("restart_service", {"service_name": "orders"}, {"accepted": True},
                      executed=True, side_effect=True)
        self.assertIsNone(engine.state.pending_postcondition)

    def test_alternating_resource_reads_do_not_invent_world_change(self):
        engine = ReasonFuseEngine()
        for resource in ["orders", "payments", "orders", "payments"]:
            result = engine.record("service_status", {"service_name": resource},
                                   {"world_state": {"service_name": resource, "service_health": "HEALTHY"}},
                                   executed=True)
        self.assertFalse(result.objective_progress)

    def test_native_provider_resume_keeps_mode_and_rejects_changed_limits(self):
        async def scenario():
            provider, session = CoreStateProvider(), AgentSession()
            saved = ReasonFuseState(reasonfuse_enabled=False, tool_call_count=3,
                                   contract_limits=RunContract().to_dict()).to_dict()
            run_id = saved["run_id"]
            with patch.dict("os.environ", {"REASONFUSE_ENABLED": "true", "REASONFUSE_CONTRACT_JSON": "{}"}):
                await provider.before_run(agent=None, session=session, context=None, state=saved)
            self.assertFalse(saved["reasonfuse_enabled"])
            self.assertEqual(saved["run_id"], run_id)
            self.assertEqual(saved["tool_call_count"], 3)
            with patch.dict("os.environ", {"REASONFUSE_CONTRACT_JSON": '{"max_tool_calls":20}'}):
                with self.assertRaises(ValueError):
                    await provider.before_run(agent=None, session=session, context=None, state=saved)
        asyncio.run(scenario())

    def test_middleware_recheck_survives_serialization_and_todo_only_stalls(self):
        async def scenario():
            session = AgentSession()
            session.state["reasonfuse_core_v1"] = ReasonFuseState().to_dict()
            middleware = ReasonFuseFunctionMiddleware()
            async def invoke(name, args, result, todo=None):
                context = FunctionInvocationContext(SimpleNamespace(name=name), args, session=session)
                async def call_next():
                    context.result = result
                    if todo:
                        session.state["todo"] = {"items": [{"id": 1, "status": todo}]}
                await middleware.process(context, call_next)
            await invoke("operations___restart_service", {"service_name": "orders"},
                         {"accepted": True, "generation": "g1"})
            session.state["reasonfuse_core_v1"] = ReasonFuseState.from_dict(
                session.state["reasonfuse_core_v1"]).to_dict()
            await invoke("operations___service_status", {"service_name": "orders"},
                         {"resource": "orders", "generation": "g1", "service_health": "HEALTHY"})
            core = session.state["reasonfuse_core_v1"]
            self.assertTrue(core["recent_actions"][-1]["useful_recheck"])
            self.assertTrue(core["last_signals"]["postcondition_delta"])
            self.assertEqual(core["last_postcondition_result"]["outcome"], "OUTCOME_VERIFIED")
            await invoke("todo_update", {}, {"message": "done"}, "completed")
            core = session.state["reasonfuse_core_v1"]
            self.assertTrue(core["last_signals"]["todo_delta"])
            self.assertEqual(core["stall_counter"], 1)
        asyncio.run(scenario())

    def test_malformed_state_fails_closed(self):
        for updates in ({"contained": "false"}, {"core_state_version": "unknown"}, {"tool_call_count": True}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                ReasonFuseState.from_dict({**ReasonFuseState().to_dict(), **updates})

    def test_decision_span_contains_structured_attributes(self):
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        provider, exporter = TracerProvider(), InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        async def scenario():
            session = AgentSession()
            session.state["reasonfuse_core_v1"] = ReasonFuseState().to_dict()
            context = FunctionInvocationContext(SimpleNamespace(name="dns_resolution"), {}, session=session)
            async def call_next():
                context.result = {"status": "INCONCLUSIVE"}
            with provider.get_tracer("core-test").start_as_current_span("dispatch"):
                await ReasonFuseFunctionMiddleware().process(context, call_next)
        try:
            asyncio.run(scenario())
            span = exporter.get_finished_spans()[0]
            self.assertIs(span.attributes["reasonfuse.evidence_delta"], False)
            self.assertEqual(span.attributes["reasonfuse.contract_version"], "reasonfuse-contract-v1")
            self.assertEqual(span.events[0].name, "reasonfuse.observation")
        finally:
            provider.shutdown()


if __name__ == "__main__":
    unittest.main()
