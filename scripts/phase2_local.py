"""Run Phase 2 deterministic core scenarios locally.

This is LOCAL_CORE evidence, not Hosted Agent acceptance. It exercises the same
engine and FunctionMiddleware used by the hosted composition without a model.
"""

from __future__ import annotations

import asyncio
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_framework import AgentSession, FunctionInvocationContext, MiddlewareTermination, tool
from reasonfuse.core.contract import RunContract
from reasonfuse.core.engine import ReasonFuseEngine
from reasonfuse.core.middleware import ReasonFuseFunctionMiddleware
from reasonfuse.core.outcome import OutcomeVerifier
from reasonfuse.core.state import ReasonFuseState


class Evidence:
    def __init__(self, batch: str):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.path = ROOT / "evidence" / "phase-02-core" / batch / f"{stamp}-local-core.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.write("START", batch=batch, evidence_layer="LOCAL_CORE")

    def write(self, event: str, **fields):
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                                     "event": event, **fields}, default=str) + "\n")


def call(engine: ReasonFuseEngine, name: str, arguments: dict, result: dict,
         *, side_effect: bool = False, todo: dict | None = None):
    decision = engine.before_dispatch(name, arguments)
    if not decision.allow:
        return decision, None
    return decision, engine.record(name, arguments, result, executed=True,
                                   side_effect=side_effect, todo_snapshot=todo)


def run_case(evidence: Evidence, name: str, callback):
    evidence.write("SCENARIO_START", scenario=name)
    try:
        result = callback()
        evidence.write("ASSERTIONS", scenario=name, **result)
        evidence.write("SCENARIO_RESULT", scenario=name, status="PASS", exit_code=0)
        return result
    except Exception as error:
        evidence.write("SCENARIO_RESULT", scenario=name, status="FAIL", exit_code=1,
                       error_type=type(error).__name__, error=str(error),
                       traceback=traceback.format_exc())
        raise


def scenario_off():
    engine = ReasonFuseEngine(ReasonFuseState(reasonfuse_enabled=False))
    executed = 0
    for _ in range(4):
        decision, observation = call(engine, "operations___dns_resolution",
                                     {"body": {"hostname": "api.reasonfuse.local"}},
                                     {"status": "INCONCLUSIVE"})
        assert decision.allow and observation.executed
        executed += 1
    assert not engine.state.contained
    return {"mode": "OFF", "executed": executed, "harness_stop": True, "fuse_tripped": False}


def scenario_on_no_progress():
    engine = ReasonFuseEngine()
    executed = 0
    for _ in range(2):
        decision, observation = call(engine, "operations___dns_resolution",
                                     {"body": {"hostname": "api.reasonfuse.local"}},
                                     {"status": "INCONCLUSIVE"})
        assert decision.allow and observation.executed
        executed += 1
    decision, _ = call(engine, "operations___dns_resolution",
                       {"body": {"hostname": "api.reasonfuse.local"}},
                       {"status": "INCONCLUSIVE"})
    assert not decision.allow and decision.reason == "NO_PROGRESS"
    assert executed == 2 and engine.state.contained
    return {"mode": "ON", "executed_before_fuse": executed,
            "fuse_reason": decision.reason, "later_dispatches": 0}


def scenario_exact_loop():
    engine = ReasonFuseEngine(ReasonFuseState(), RunContract(max_stalled_steps=10, required_objective_progress_interval=10))
    for _ in range(2):
        decision, _ = call(engine, "operations___dns_resolution",
                           {"body": {"hostname": "api.reasonfuse.local"}},
                           {"status": "INCONCLUSIVE"})
        assert decision.allow
    decision, _ = call(engine, "operations___dns_resolution",
                       {"body": {"hostname": "api.reasonfuse.local"}},
                       {"status": "INCONCLUSIVE"})
    assert decision.reason == "EXACT_LOOP"
    return {"fuse_reason": decision.reason, "external_dispatch_after_trip": 0}


def scenario_oscillation():
    engine = ReasonFuseEngine(ReasonFuseState(), RunContract(max_stalled_steps=10, required_objective_progress_interval=10))
    for name in ["tool_a", "tool_b", "tool_a"]:
        decision, _ = call(engine, name, {"body": {"value": name}}, {"status": "INCONCLUSIVE"})
        assert decision.allow
    decision, _ = call(engine, "tool_b", {"body": {"value": "tool_b"}}, {"status": "INCONCLUSIVE"})
    assert decision.reason == "OSCILLATING"
    return {"fuse_reason": decision.reason, "external_dispatch_after_trip": 0}


def scenario_retrieval_churn():
    engine = ReasonFuseEngine(ReasonFuseState(), RunContract(max_stalled_steps=10, required_objective_progress_interval=10))
    for query in ["database failure", "db connectivity", "database issue"]:
        decision, _ = call(engine, "operations___retrieval_fixture", {"body": {"query": query}}, {
            "query": query, "retrieval": {"source_keys": ["A", "B"], "knowledge_base_version": "fixture-v1"}
        })
        assert decision.allow
    assert engine.state.contained and engine.state.fuse_reason == "RETRIEVAL_CHURN"
    return {"label": "LIVE_HOSTED_WITH_DETERMINISTIC_RETRIEVAL_FIXTURE_PENDING",
            "fuse_reason": engine.state.fuse_reason, "foundry_iq": "NOT VERIFIED"}


def scenario_useful_recheck():
    engine = ReasonFuseEngine()
    restart, _ = call(engine, "restart_service", {"body": {"service_name": "orders"}}, {
        "accepted": True, "status_code": 202, "generation": "g1",
        "world_state": {"service_name": "orders", "service_health": "UNHEALTHY"},
    }, side_effect=True)
    assert restart.allow
    status, observation = call(engine, "service_status", {"body": {"service_name": "orders"}}, {
        "resource": "orders", "service_name": "orders", "service_health": "HEALTHY",
        "generation": "g1", "world_state": {"service_name": "orders", "service_health": "HEALTHY"},
    })
    assert status.allow and observation.signals["useful_recheck"]
    outcome = OutcomeVerifier().verify("restart_service", {"accepted": True}, {
        "resource": "orders", "service_health": "HEALTHY"}, requested_resource="orders")
    engine.set_outcome(outcome)
    assert outcome["outcome"] == "OUTCOME_VERIFIED" and not engine.state.contained
    return {"useful_recheck": True, "outcome": outcome["outcome"], "side_effects": engine.state.side_effect_count}


def scenario_todo_only():
    engine = ReasonFuseEngine(ReasonFuseState(), RunContract(max_stalled_steps=10, required_objective_progress_interval=10))
    for index, status in enumerate(["OPEN", "IN_PROGRESS", "COMPLETED"], start=1):
        decision, observation = call(engine, "operations___dns_resolution",
                                     {"body": {"hostname": f"api-{index}.reasonfuse.local"}},
                                     {"status": "INCONCLUSIVE"}, todo={"status": status})
        assert decision.allow and not observation.objective_progress
    return {"todo_delta_seen": True, "objective_progress": False,
            "progress_state": engine.state.progress_state}


def scenario_budget():
    engine = ReasonFuseEngine(ReasonFuseState(), RunContract(max_tool_calls=2, max_stalled_steps=10,
                                                           required_objective_progress_interval=10))
    for _ in range(2):
        decision, _ = call(engine, "operations___dns_resolution",
                           {"body": {"hostname": "api.reasonfuse.local"}}, {"status": "INCONCLUSIVE"})
        assert decision.allow
    decision, _ = call(engine, "operations___dns_resolution",
                       {"body": {"hostname": "other.reasonfuse.local"}}, {"status": "INCONCLUSIVE"})
    assert decision.reason == "BUDGET_EXHAUSTED"
    return {"fuse_reason": decision.reason, "tool_calls": engine.state.tool_call_count}


def scenario_outcomes():
    verifier = OutcomeVerifier()
    accepted = {"accepted": True, "status_code": 202}
    failed = verifier.verify("restart_service", accepted,
                             {"resource": "orders", "service_health": "UNHEALTHY"},
                             requested_resource="orders")
    unknown = verifier.verify("restart_service", accepted, None, requested_resource="orders")
    verified = verifier.verify("restart_service", accepted,
                               {"resource": "orders", "service_health": "HEALTHY"},
                               requested_resource="orders")
    assert failed["outcome"] == "POSTCONDITION_FAILED"
    assert unknown["outcome"] == "OUTCOME_UNKNOWN"
    assert verified["outcome"] == "OUTCOME_VERIFIED"
    return {"postcondition_failed": failed["outcome"], "unknown": unknown["outcome"],
            "verified": verified["outcome"]}


async def scenario_middleware():
    session = AgentSession()
    session.state["reasonfuse_core_v1"] = ReasonFuseState().to_dict()
    calls = 0

    @tool
    def operations___dns_resolution(body: dict) -> str:
        return json.dumps({"status": "INCONCLUSIVE"})

    async def invoke(context):
        nonlocal calls
        calls += 1
        context.result = {"status": "INCONCLUSIVE"}

    middleware = ReasonFuseFunctionMiddleware()
    for _ in range(2):
        context = FunctionInvocationContext(operations___dns_resolution,
                                            {"body": {"hostname": "api.reasonfuse.local"}}, session=session)
        try:
            await middleware.process(context, lambda context=context: invoke(context))
        except MiddlewareTermination:
            pass
    context = FunctionInvocationContext(operations___dns_resolution,
                                        {"body": {"hostname": "api.reasonfuse.local"}}, session=session)
    try:
        await middleware.process(context, lambda context=context: invoke(context))
    except MiddlewareTermination:
        pass
    assert calls == 2
    assert session.state["reasonfuse_core_v1"]["fuse_reason"] == "NO_PROGRESS"
    return {"middleware_path": True, "calls_before_containment": calls,
            "fuse_reason": session.state["reasonfuse_core_v1"]["fuse_reason"]}


def main():
    evidence = Evidence("local-" + datetime.now(timezone.utc).strftime("%Y%m%d"))
    cases = {
        "A_off_no_progress": scenario_off,
        "B_on_no_progress": scenario_on_no_progress,
        "C_exact_loop": scenario_exact_loop,
        "D_oscillation": scenario_oscillation,
        "E_retrieval_churn": scenario_retrieval_churn,
        "F_useful_recheck": scenario_useful_recheck,
        "G_todo_only": scenario_todo_only,
        "H_budget_exhaustion": scenario_budget,
        "I_outcomes": scenario_outcomes,
    }
    for name, callback in cases.items():
        run_case(evidence, name, callback)
    run_case(evidence, "J_middleware_path", lambda: asyncio.run(scenario_middleware()))
    evidence.write("RESULT", status="PASS", exit_code=0, evidence_layer="LOCAL_CORE")
    print(f"PHASE2_LOCAL_PASS {evidence.path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"PHASE2_LOCAL_FAIL {type(error).__name__}: {error}", file=sys.stderr)
        raise
