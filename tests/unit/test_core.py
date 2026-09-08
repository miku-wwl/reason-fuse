import math
import unittest

from reasonfuse.core.contract import RunContract
from reasonfuse.core.detectors import UsefulRecheckClassifier, exact_loop, oscillation, retrieval_churn
from reasonfuse.core.engine import ReasonFuseEngine
from reasonfuse.core.fingerprint import canonical_json, tool_fingerprint
from reasonfuse.core.middleware import _result
from reasonfuse.core.outcome import OutcomeVerifier
from reasonfuse.core.progress import world_state_delta
from reasonfuse.core.state import ReasonFuseState


class FingerprintTests(unittest.TestCase):
    def test_dictionary_order_is_semantically_irrelevant(self):
        self.assertEqual(tool_fingerprint("tool", {"a": 1, "b": 2}),
                         tool_fingerprint("tool", {"b": 2, "a": 1}))

    def test_array_order_and_missing_are_semantically_relevant(self):
        self.assertNotEqual(canonical_json({"items": [1, 2]}), canonical_json({"items": [2, 1]}))
        self.assertNotEqual(canonical_json({"a": None}), canonical_json({}))

    def test_non_finite_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            canonical_json({"value": math.nan})


class DetectorTests(unittest.TestCase):
    def test_exact_loop_waits_for_three_identical_calls(self):
        self.assertFalse(exact_loop(["a", "a"], [False, False]).tripped)
        self.assertEqual(exact_loop(["a", "a", "a"], [False, False, False]).reason, "EXACT_LOOP")

    def test_period_two_oscillation(self):
        result = oscillation(["a", "b", "a", "b"], [False] * 4)
        self.assertEqual(result.reason, "OSCILLATING")

    def test_retrieval_churn_requires_different_queries_and_same_evidence(self):
        result = retrieval_churn([
            {"query": "one", "source_keys": ["A", "B"]},
            {"query": "two", "source_keys": ["B", "A"]},
            {"query": "three", "source_keys": ["A", "B"]},
        ])
        self.assertEqual(result.reason, "RETRIEVAL_CHURN")

    def test_useful_recheck_is_one_bounded_obligation(self):
        classifier = UsefulRecheckClassifier()
        classifier.accepted_side_effect("restart_service", "orders", "g1")
        self.assertEqual(classifier.classify("service_status", "orders", "g1").reason, "USEFUL_RECHECK")
        self.assertFalse(classifier.classify("service_status", "orders", "g1").tripped)


class EngineTests(unittest.TestCase):
    @staticmethod
    def no_progress(engine, name="operations___dns_resolution", query="api"):
        args = {"body": {"hostname": query}}
        decision = engine.before_dispatch(name, args)
        if decision.allow:
            engine.record(name, args, {"status": "INCONCLUSIVE"}, executed=True)
        return decision

    def test_off_does_not_block(self):
        engine = ReasonFuseEngine(ReasonFuseState(reasonfuse_enabled=False))
        for _ in range(5):
            self.assertTrue(self.no_progress(engine).allow)
        self.assertFalse(engine.state.contained)

    def test_on_no_progress_contains_after_completed_second_call(self):
        engine = ReasonFuseEngine()
        self.assertTrue(self.no_progress(engine).allow)
        self.assertTrue(self.no_progress(engine).allow)
        self.assertTrue(engine.state.contained)
        blocked = self.no_progress(engine)
        self.assertFalse(blocked.allow)
        self.assertEqual(blocked.reason, "NO_PROGRESS")

    def test_exact_loop_has_precedence_when_stall_budget_is_raised(self):
        contract = RunContract(max_stalled_steps=10, required_objective_progress_interval=10)
        engine = ReasonFuseEngine(ReasonFuseState(), contract)
        self.assertTrue(self.no_progress(engine).allow)
        self.assertTrue(self.no_progress(engine).allow)
        blocked = self.no_progress(engine)
        self.assertFalse(blocked.allow)
        self.assertEqual(blocked.reason, "EXACT_LOOP")

    def test_oscillation_and_churn_scenarios(self):
        contract = RunContract(max_stalled_steps=10, required_objective_progress_interval=10)
        engine = ReasonFuseEngine(ReasonFuseState(), contract)
        for name in ["a", "b", "a"]:
            args = {"body": {"value": name}}
            self.assertTrue(engine.before_dispatch(name, args).allow)
            engine.record(name, args, {"status": "INCONCLUSIVE"}, executed=True)
        blocked = engine.before_dispatch("b", {"body": {"value": "b"}})
        self.assertEqual(blocked.reason, "OSCILLATING")

        engine = ReasonFuseEngine(ReasonFuseState(), contract)
        for query in ["one", "two", "three"]:
            args = {"body": {"query": query}}
            self.assertTrue(engine.before_dispatch("retrieval_fixture", args).allow)
            observation = engine.record("retrieval_fixture", args, {
                "query": query,
                "retrieval": {"source_keys": ["A", "B"], "knowledge_base_version": "v1"},
            }, executed=True)
        self.assertTrue(engine.state.contained)
        self.assertEqual(observation.fuse_reason, "RETRIEVAL_CHURN")

    def test_retrieval_churn_precedes_stall_budget_on_third_query(self):
        engine = ReasonFuseEngine()
        for query in ["one", "two", "three"]:
            args = {"body": {"query": query}}
            self.assertTrue(engine.before_dispatch("retrieval_fixture", args).allow)
            engine.record("retrieval_fixture", args, {
                "query": query,
                "retrieval": {"source_keys": ["A", "B"], "knowledge_base_version": "v1"},
            }, executed=True)
        self.assertTrue(engine.state.contained)
        self.assertEqual(engine.state.fuse_reason, "RETRIEVAL_CHURN")

    def test_state_restores_changed_values(self):
        state = ReasonFuseState(step_index=4, tool_call_count=3, run_id="stable", reasonfuse_enabled=True)
        restored = ReasonFuseState.from_dict(state.to_dict())
        self.assertEqual(restored.run_id, "stable")
        self.assertEqual(restored.step_index, 4)
        self.assertEqual(restored.tool_call_count, 3)


class OutcomeTests(unittest.TestCase):
    def test_accepted_202_is_not_success_without_postcondition(self):
        verifier = OutcomeVerifier()
        accepted = {"accepted": True, "status_code": 202}
        self.assertEqual(verifier.verify("restart_service", accepted, {
            "resource": "orders", "service_health": "UNHEALTHY"
        }, requested_resource="orders")["outcome"], "POSTCONDITION_FAILED")
        self.assertEqual(verifier.verify("restart_service", accepted, None,
                                         requested_resource="orders")["outcome"], "OUTCOME_UNKNOWN")
        self.assertEqual(verifier.verify("restart_service", accepted, {
            "resource": "orders", "service_health": "HEALTHY"
        }, requested_resource="orders")["outcome"], "OUTCOME_VERIFIED")
        self.assertEqual(verifier.verify("restart_service", accepted, {
            "resource": "payments", "service_health": "HEALTHY"
        }, requested_resource="orders")["outcome"], "OUTCOME_UNKNOWN")
        for status in ["timeout", "stale", "malformed", "unavailable"]:
            self.assertEqual(verifier.verify("restart_service", accepted, {
                "resource": "orders", "status": status
            }, requested_resource="orders")["outcome"], "OUTCOME_UNKNOWN")


class ProgressTests(unittest.TestCase):
    def test_request_ids_and_counters_are_not_world_progress(self):
        before = {"service_health": "UNHEALTHY", "request_id": "one", "counter": 1}
        after = {"service_health": "UNHEALTHY", "request_id": "two", "counter": 2}
        self.assertFalse(world_state_delta(before, after))


class MiddlewareNormalizationTests(unittest.TestCase):
    def test_toolbox_content_list_is_normalized_to_json_object(self):
        self.assertEqual(
            _result([{"type": "text", "text":
                      '{"retrieval":{"source_keys":["A"]},"query":"one"}'}]),
            {"retrieval": {"source_keys": ["A"]}, "query": "one"},
        )


if __name__ == "__main__":
    unittest.main()
