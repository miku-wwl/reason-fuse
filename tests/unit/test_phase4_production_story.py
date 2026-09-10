from __future__ import annotations

import json
from pathlib import Path

from scripts.phase4_production_story import (
    _affinity_simulation,
    _candidate_regression_pair,
    _judge_view,
    _local_apim_config,
    _rollback,
    _sse_simulation,
)


def test_phase4_iac_and_stream_contracts_are_present() -> None:
    apim = _local_apim_config()
    assert apim["status"] == "CONSTRUCTION_READY"
    assert apim["configured_weights"] == {"stable": 95, "candidate": 5}
    assert _sse_simulation()["incremental_arrival"] is True


def test_phase4_affinity_is_sticky_and_rollback_is_stable_only() -> None:
    affinity = _affinity_simulation()
    assert affinity["status"] == "PASS"
    assert affinity["persistent_client"]["sticky"] is True
    rollback = _rollback()
    assert rollback["after"] == {"stable": 100, "candidate": 0}
    assert rollback["new_session_role_after_rollback"] == "stable"


def test_phase4_candidate_fixture_has_a_controlled_difference() -> None:
    dataset = Path("benchmark/datasets/reasonfuse_v2.jsonl")
    source = next(json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip() and json.loads(line)["scenario_id"] == "H-007")
    stable, candidate = _candidate_regression_pair(source)
    assert [action["tool_name"] for action in stable["actions"]] == ["dns_resolution", "service_status"]
    assert [action["tool_name"] for action in candidate["actions"]] == ["dns_resolution", "dns_resolution", "dns_resolution"]
    assert stable["toolbox_version"] == candidate["toolbox_version"]
    assert stable["knowledge_base_version"] == candidate["knowledge_base_version"]


def test_judge_mode_reads_actual_run_state() -> None:
    run = {
        "valid": True,
        "release_role": "candidate",
        "trace_id": "local-test",
        "actual": {"trip": True, "failure_type": "EXACT_LOOP", "objective_progress_events": 0, "useful_recheck": False, "containment_latency_ms": 1.2},
        "_scenario_actions": [{"approved": True}],
        "raw_events": [{
            "tool_name": "dns_resolution",
            "observation": {"signals": {"evidence_delta": False, "world_state_delta": False, "retrieval_delta": False, "todo_delta": False, "postcondition_delta": False}},
            "state": {"trajectory_state": "STALLED"},
        }],
    }
    view = _judge_view(run)
    assert view["reasonfuse_decision"] == "BLOCK"
    assert view["fuse_reason"] == "EXACT_LOOP"
    assert view["release_role"] == "candidate"
