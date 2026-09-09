"""Execute one dataset scenario against the local ReasonFuse engine."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from reasonfuse.core.contract import RunContract
from reasonfuse.core.engine import ReasonFuseEngine
from reasonfuse.core.outcome import OutcomeVerifier
from reasonfuse.core.state import ReasonFuseState
from reasonfuse.core.fingerprint import tool_fingerprint

from benchmark.runners.reset_scenario import reset_scenario


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "NOT AVAILABLE"


def execute_scenario(scenario: dict[str, Any], repetition: int, *, enabled: bool = True, mode: str = "ON") -> dict[str, Any]:
    scenario_id = scenario["scenario_id"]
    run_key = f"{scenario_id}|{repetition}|{mode}"
    run_digest = _digest(run_key)
    reset = reset_scenario(scenario, repetition, mode)
    if reset.get("reset") != "RESET_COMPLETE" or reset.get("network") != "DISABLED":
        raise RuntimeError("SCENARIO_RESET_ERROR: reset did not complete in offline fixture")
    if any(value != 0 for value in reset.get("counters", {}).values()):
        raise RuntimeError("SCENARIO_RESET_ERROR: reset counters were not zero")
    contract_data = dict(scenario.get("contract_overrides", {}))
    contract_data["version"] = scenario["run_contract_version"]
    contract = RunContract.from_dict(contract_data)
    state = ReasonFuseState(
        run_id=f"run-benchmark-{run_digest}",
        conversation_id=reset["conversation_id"],
        agent_session_id=f"agent-benchmark-{run_digest}",
        framework_session_id=f"framework-benchmark-{run_digest}",
        reasonfuse_enabled=enabled,
        contract_limits=contract.to_dict(),
        run_contract_version=contract.version,
        world_state_snapshot=reset["world_state"],
    )
    engine = ReasonFuseEngine(state, contract)
    verifier = OutcomeVerifier()
    events: list[dict[str, Any]] = []
    containment_latency_ms = 0.0
    containment_step: int | None = None
    objective_progress_events = 0
    useful_recheck = False
    outcome: str | None = None
    executed_fingerprints: list[str] = []
    started = time.perf_counter()

    for step, action in enumerate(scenario["actions"], 1):
        tool_name = action["tool_name"]
        arguments = action["arguments"]
        decision = engine.before_dispatch(tool_name, arguments)
        event: dict[str, Any] = {"step": step, "tool_name": tool_name, "mode": mode,
                                 "decision": {"allow": decision.allow, "reason": decision.reason}}
        if not decision.allow:
            if containment_step is None:
                containment_step = state.step_index
                containment_latency_ms = (time.perf_counter() - started) * 1000
            event["executed"] = False
            event["observation"] = None
            event["state"] = state.to_dict()
            events.append(event)
            break
        observation = engine.record(
            tool_name,
            arguments,
            action["result"],
            executed=True,
            side_effect=bool(action.get("side_effect", False)),
            approved=bool(action.get("approved", False)),
            todo_snapshot=action.get("todo_snapshot"),
        )
        executed_fingerprints.append(tool_fingerprint(tool_name, arguments))
        objective_progress_events += int(observation.objective_progress)
        if observation.signals.get("useful_recheck"):
            # A recheck is useful for this benchmark only when it proves the
            # requested postcondition, not merely when it consumes a slot.
            useful_recheck = True
        if action.get("verify_postcondition"):
            pending = state.pending_postcondition
            if pending:
                verified = verifier.verify(
                    pending["action"], pending["accepted_result"], action["result"],
                    requested_resource=pending["resource"],
                )
                engine.set_outcome(verified)
                outcome = verified["outcome"]
                if outcome != "OUTCOME_VERIFIED":
                    useful_recheck = False
                event["outcome"] = verified
        event["executed"] = True
        event["observation"] = asdict(observation)
        event["state"] = state.to_dict()
        events.append(event)
        if state.contained and containment_step is None:
            containment_step = state.step_index
            containment_latency_ms = (time.perf_counter() - started) * 1000
            break

    actual_trip = bool(state.contained)
    actual = {
        "trip": actual_trip,
        "failure_type": state.fuse_reason if actual_trip else None,
        "outcome": outcome,
        "useful_recheck": useful_recheck,
        "healthy_completion": not actual_trip,
        "steps": state.step_index,
        "tool_calls": state.tool_call_count,
        "side_effects": state.side_effect_count,
        "blocked_proposals": state.blocked_proposal_count,
        "containment_step": containment_step,
        "containment_latency_ms": round(containment_latency_ms, 6),
        "objective_progress_events": objective_progress_events,
        "stall_events": state.stall_counter,
        "requested_actions": len(scenario["actions"]),
        "redundant_tool_calls": max(0, len(executed_fingerprints) - len(set(executed_fingerprints))),
    }
    timestamp = datetime.now(timezone.utc).isoformat()
    expected = scenario["expected"]
    return {
        "valid": True,
        "error": None,
        "execution_layer": "LOCAL_DETERMINISTIC",
        "fixture_scope": True,
        "hosted": False,
        "scenario_id": scenario_id,
        "scenario_version": scenario["scenario_version"],
        "category": scenario["category"],
        "description": scenario["description"],
        "repetition": repetition,
        "mode": mode,
        "run_id": state.run_id,
        "conversation_id": state.conversation_id,
        "agent_session_id": state.agent_session_id,
        "framework_session_id": state.framework_session_id,
        "expected": expected,
        "actual": actual,
        # Flat fields mirror the Phase 3 run-result contract and keep the
        # normalized JSONL useful without requiring nested-field knowledge.
        "expected_failure_type": expected["expected_failure_type"],
        "actual_failure_type": actual["failure_type"],
        "expected_trip": expected["should_trip"],
        "actual_trip": actual["trip"],
        "expected_useful_recheck": expected["expected_useful_recheck"],
        "actual_useful_recheck": actual["useful_recheck"],
        "expected_outcome": expected["expected_outcome"],
        "actual_outcome": actual["outcome"],
        "healthy_completion_expected": expected["healthy_completion_expected"],
        "healthy_completion_actual": actual["healthy_completion"],
        "steps": actual["steps"],
        "tool_calls": actual["tool_calls"],
        "side_effects": actual["side_effects"],
        "containment_step": actual["containment_step"],
        "containment_latency_ms": actual["containment_latency_ms"],
        "objective_progress_events": actual["objective_progress_events"],
        "stall_events": actual["stall_events"],
        "tokens_in": "NOT AVAILABLE",
        "tokens_out": "NOT AVAILABLE",
        "estimated_cost": "NOT AVAILABLE",
        "versions": {"run_contract": contract.version, "toolbox": scenario["toolbox_version"],
                      "knowledge_base": scenario["knowledge_base_version"], "agent": scenario["agent_version"],
                      "model": scenario["model_version"]},
        "source_manifest": {"git_commit": _git_commit(), "dataset_version": scenario["scenario_version"]},
        "reset": reset,
        "reasonfuse_contract_version": contract.version,
        "agent_version": scenario["agent_version"],
        "model_version": scenario["model_version"],
        "prompt_version": "reasonfuse-phase3-prompt-v1",
        "toolbox_version": scenario["toolbox_version"],
        "knowledge_base_version": scenario["knowledge_base_version"],
        "trace_id": "NOT_AVAILABLE_LOCAL",
        "tokens": "NOT AVAILABLE",
        "cost": "NOT AVAILABLE",
        "timestamp": timestamp,
        "timestamp_utc": timestamp,
        "raw_events": events,
    }
