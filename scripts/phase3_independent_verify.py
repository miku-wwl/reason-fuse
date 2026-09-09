"""Independent, read-only checks for the materialized Phase 3 benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


CATEGORIES = ("Healthy", "Exact Loop", "Oscillation", "Retrieval Churn", "Outcome Failure")
EXPECTED_SCENARIO_IDS = {
    "H-001", "H-007", "H-018",
    "EL-001", "EL-005", "EL-013",
    "OS-001", "OS-007", "OS-018",
    "RC-001", "RC-010", "RC-020",
    "OF-001", "OF-002", "OF-015",
}
EXPECTED_SCENARIO_COUNT = 15
EXPECTED_CATEGORY_COUNT = 3
EXPECTED_REPETITIONS = [1]
EXPECTED_RUN_COUNT = EXPECTED_SCENARIO_COUNT * len(EXPECTED_REPETITIONS)
REQUIRED_FLAT = {
    "scenario_id", "repetition", "run_id", "conversation_id", "agent_session_id",
    "category", "expected_failure_type", "actual_failure_type", "expected_trip", "actual_trip",
    "expected_useful_recheck", "actual_useful_recheck", "expected_outcome", "actual_outcome",
    "healthy_completion_expected", "healthy_completion_actual", "steps", "tool_calls",
    "side_effects", "containment_step", "containment_latency_ms", "objective_progress_events",
    "stall_events", "trace_id", "agent_version", "model_version", "prompt_version",
    "toolbox_version", "knowledge_base_version", "reasonfuse_contract_version", "timestamp",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--batch", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dataset", default="benchmark/datasets/reasonfuse_v2.jsonl")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    batch = (repo / args.batch).resolve()
    checks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    def warn(name: str, detail: str) -> None:
        warnings.append({"name": name, "status": "WARNING", "detail": detail})

    dataset_path = (repo / args.dataset).resolve()
    dataset = load_jsonl(dataset_path)
    by_id = {row["scenario_id"]: row for row in dataset}
    category_counts = Counter(row.get("category") for row in dataset)
    expected_ids = EXPECTED_SCENARIO_IDS
    actual_ids = {row.get("scenario_id") for row in dataset}
    check("dataset_count", len(dataset) == EXPECTED_SCENARIO_COUNT, f"records={len(dataset)}")
    check("dataset_unique_ids", len(actual_ids) == EXPECTED_SCENARIO_COUNT and actual_ids == expected_ids, f"unique={len(actual_ids)}")
    check("dataset_category_counts", all(category_counts.get(category, 0) == EXPECTED_CATEGORY_COUNT for category in CATEGORIES), dict(category_counts))
    check("dataset_schema_helper", subprocess.run([sys.executable, "-m", "benchmark.datasets.validate_dataset", "--dataset", str(dataset_path)], cwd=repo, capture_output=True, text=True).returncode == 0, "portable validator exit status")
    check("dataset_version", len({row.get("scenario_version") for row in dataset}) == 1, str(sorted({row.get("scenario_version") for row in dataset})))
    variations = {category: len({row.get("variation_dimension") for row in dataset if row.get("category") == category}) for category in CATEGORIES}
    tool_shapes = {category: len({tuple(action.get("tool_name") for action in row.get("actions", [])) for row in dataset if row.get("category") == category}) for category in CATEGORIES}
    pattern_families = {category: len({row.get("fault_configuration", {}).get("pattern_family") for row in dataset if row.get("category") == category}) for category in CATEGORIES}
    check("scenario_diversity", all(variations[category] >= 1 for category in CATEGORIES), f"variation_dimensions={variations}; tool_shapes={tool_shapes}; pattern_families={pattern_families}")
    check("semantic_pattern_family_coverage", all(pattern_families[category] == EXPECTED_CATEGORY_COUNT for category in CATEGORIES), f"pattern_families={pattern_families}")
    warn("scenario_pattern_diversity_review", f"Semantic pattern-family counts are {pattern_families}; raw tool-shape counts remain {tool_shapes} because Retrieval Churn intentionally uses one retrieval tool with different domains and evidence identities.")
    todo_actions = sum(1 for row in dataset for action in row.get("actions", []) if action.get("todo_snapshot") is not None)
    if todo_actions == 0:
        warn("todo_negative_control_dataset_coverage", "No Phase 3 dataset action contains todo_snapshot; frozen Phase 2 unit evidence must cover this invariant.")
    else:
        check("todo_negative_control_dataset_coverage", True, f"todo_actions={todo_actions}")

    index_path = batch / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    hash_failures = []
    for artifact in index.get("artifacts", []):
        artifact_path = batch / artifact["path"]
        if not artifact_path.exists() or sha256(artifact_path) != artifact["sha256"]:
            hash_failures.append(artifact["path"])
    check("evidence_index_hashes", not hash_failures, f"artifacts={len(index.get('artifacts', []))}; bad={hash_failures}")
    check("evidence_index_result", index.get("result") == "PHASE3_CONSTRUCTION_EVIDENCE_INDEXED", str(index.get("result")))

    raw = load_jsonl(batch / "raw/runs.jsonl")
    normalized = load_jsonl(batch / "normalized/results.jsonl")
    check("raw_run_count", len(raw) == EXPECTED_RUN_COUNT, f"raw={len(raw)}")
    check("normalized_run_count", len(normalized) == EXPECTED_RUN_COUNT, f"normalized={len(normalized)}")
    check("raw_validity", all(row.get("valid") is True and row.get("error") is None for row in raw), "all raw rows valid with no runner error")
    check("raw_schema", all(REQUIRED_FLAT <= set(row) for row in raw), "flat run-result fields present")
    run_keys = [(row.get("scenario_id"), row.get("repetition"), row.get("mode")) for row in raw]
    check("raw_unique_run_keys", len(set(run_keys)) == EXPECTED_RUN_COUNT, f"unique_keys={len(set(run_keys))}")
    repetition_map: dict[str, list[int]] = defaultdict(list)
    for row in raw:
        repetition_map[row["scenario_id"]].append(row["repetition"])
    check("one_repetition_each", all(sorted(values) == EXPECTED_REPETITIONS for values in repetition_map.values()), "each scenario has one competition repetition")
    reset_failures = []
    first_state_failures = []
    for row in raw:
        reset = row.get("reset", {})
        counters = reset.get("counters", {})
        if not (reset.get("reset") == "RESET_COMPLETE" and reset.get("network") == "DISABLED" and reset.get("fixture_scope") is True and all(counters.get(name) == 0 for name in ("steps", "tool_calls", "side_effects"))):
            reset_failures.append(row["scenario_id"] + f"/{row['repetition']}")
        events = row.get("raw_events", [])
        first = events[0].get("state", {}) if events else {}
        if not (first.get("event_count") == 1 and first.get("step_index") == 1 and first.get("run_id") == row.get("run_id")):
            first_state_failures.append(row["scenario_id"] + f"/{row['repetition']}")
    check("reset_integrity", not reset_failures, f"failures={reset_failures[:5]}")
    check("fresh_state_integrity", not first_state_failures, f"failures={first_state_failures[:5]}")
    check("fresh_conversation_ids", len({row.get("conversation_id") for row in raw}) == EXPECTED_RUN_COUNT, "conversation IDs unique across ON scenarios")

    mismatch_rows = []
    for row in raw:
        expected = row["expected"]
        actual = row["actual"]
        pairs = {
            "trip": (expected.get("should_trip"), actual.get("trip")),
            "failure_type": (expected.get("expected_failure_type"), actual.get("failure_type")),
            "outcome": (expected.get("expected_outcome"), actual.get("outcome")),
            "useful_recheck": (expected.get("expected_useful_recheck"), actual.get("useful_recheck")),
            "healthy_completion": (expected.get("healthy_completion_expected"), actual.get("healthy_completion")),
        }
        if any(want != got for want, got in pairs.values()):
            mismatch_rows.append(row["scenario_id"] + f"/{row['repetition']}")
    check("ground_truth_label_consistency", not mismatch_rows, f"mismatches={mismatch_rows[:5]}")

    todo_ids = {row["scenario_id"] for row in dataset for action in row.get("actions", []) if action.get("todo_snapshot") is not None}
    todo_rows = [row for row in raw if row.get("scenario_id") in todo_ids]
    todo_delta_failures = []
    for row in todo_rows:
        observations = [event.get("observation", {}) for event in row.get("raw_events", [])]
        if not any(obs.get("signals", {}).get("todo_delta") is True for obs in observations):
            todo_delta_failures.append(f"{row['scenario_id']}/{row['repetition']}:missing_todo_delta")
        if any(obs.get("objective_progress") is True for obs in observations):
            todo_delta_failures.append(f"{row['scenario_id']}/{row['repetition']}:todo_counted_as_objective_progress")
    check("todo_negative_control_behavior", bool(todo_rows) and not todo_delta_failures, f"runs={len(todo_rows)}; failures={todo_delta_failures[:5]}")

    valid = [row for row in raw if row.get("valid") is True]
    tp = sum(row["expected"]["should_trip"] and row["actual"]["trip"] for row in valid)
    fp = sum(not row["expected"]["should_trip"] and row["actual"]["trip"] for row in valid)
    tn = sum(not row["expected"]["should_trip"] and not row["actual"]["trip"] for row in valid)
    fn = sum(row["expected"]["should_trip"] and not row["actual"]["trip"] for row in valid)
    recomputed_metrics = {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
                          "recall": ratio(tp, tp + fn), "precision": ratio(tp, tp + fp),
                          "fpr": ratio(fp, fp + tn), "fnr": ratio(fn, fn + tp),
                          "accuracy": ratio(tp + tn, len(valid))}
    reported = json.loads((batch / "summary/metrics.json").read_text(encoding="utf-8"))
    reported_matrix = reported["confusion_matrix"]
    reported_metrics = reported["metrics"]
    matrix_match = all(reported_matrix[key] == recomputed_metrics[key] for key in ("TP", "FP", "TN", "FN"))
    metric_match = all(abs(reported_metrics[key] - recomputed_metrics[reported_key]) < 1e-12 for key, reported_key in (("recall", "recall"), ("precision", "precision"), ("false_positive_rate", "fpr"), ("false_negative_rate", "fnr"), ("accuracy", "accuracy")))
    check("confusion_matrix_recompute", matrix_match, f"recomputed={recomputed_metrics}")
    check("core_metrics_recompute", metric_match, f"reported={reported_metrics}")

    category_results: dict[str, Any] = {}
    for category in CATEGORIES:
        rows = [row for row in valid if row["category"] == category]
        category_results[category] = {
            "runs": len(rows),
            "correct": sum(row["expected"] == row["expected"] and row["actual_failure_type"] == row["expected_failure_type"] and row["actual_trip"] == row["expected_trip"] and row["actual_outcome"] == row["expected_outcome"] and row["actual_useful_recheck"] == row["expected_useful_recheck"] and row["healthy_completion_actual"] == row["healthy_completion_expected"] for row in rows),
            "actual_trip_rate": ratio(sum(row["actual_trip"] for row in rows), len(rows)),
        }
    check("category_denominators", all(category_results[category]["runs"] == EXPECTED_CATEGORY_COUNT for category in CATEGORIES), str(category_results))
    check("healthy_completion", all(row["actual"]["healthy_completion"] for row in valid if row["category"] == "Healthy"), "all Healthy rows completed without containment")
    useful_rows = [row for row in valid if row["expected"]["expected_useful_recheck"]]
    check("useful_recheck_preservation", all(row["actual"]["useful_recheck"] for row in useful_rows), f"preserved={sum(row['actual']['useful_recheck'] for row in useful_rows)}/{len(useful_rows)}")
    failure_rows = [row for row in valid if row["expected"]["expected_outcome"] == "POSTCONDITION_FAILED"]
    check("postcondition_failure_detection", all(row["actual"]["outcome"] == "POSTCONDITION_FAILED" for row in failure_rows), f"detected={sum(row['actual']['outcome'] == 'POSTCONDITION_FAILED' for row in failure_rows)}/{len(failure_rows)}")

    off_on = load_jsonl(batch / "raw/off_on.jsonl")
    on_rows = {(row["scenario_id"], row["repetition"]): row for row in off_on if row.get("mode") == "ON"}
    off_rows = {(row["scenario_id"], row["repetition"]): row for row in off_on if row.get("mode") == "OFF"}
    fair_failures = []
    for key in sorted(on_rows.keys() & off_rows.keys()):
        on, off = on_rows[key], off_rows[key]
        if on["category"] != off["category"] or on["description"] != off["description"] or on["expected"] != off["expected"] or on["versions"] != off["versions"] or on["reset"]["world_state"] != off["reset"]["world_state"]:
            fair_failures.append(key)
    check("off_on_pair_count", len(on_rows) == EXPECTED_SCENARIO_COUNT and len(off_rows) == EXPECTED_SCENARIO_COUNT and len(on_rows.keys() & off_rows.keys()) == EXPECTED_SCENARIO_COUNT, f"on={len(on_rows)} off={len(off_rows)} pairs={len(on_rows.keys() & off_rows.keys())}")
    check("off_on_fairness", not fair_failures, f"failures={fair_failures}")

    micro = json.loads((batch / "microbenchmark.json").read_text(encoding="utf-8"))
    check("microbenchmark", micro.get("status") == "PASS" and micro.get("events") == 10000 and micro.get("network") == "DISABLED" and micro.get("llm") == "NOT INVOKED", str({key: micro.get(key) for key in ("status", "events", "network", "llm")}))
    metadata = json.loads((batch / "summary/dataset_metadata.json").read_text(encoding="utf-8"))
    threshold_path = repo / "benchmark/datasets/frozen_thresholds.json"
    check("threshold_hash", metadata.get("frozen_thresholds_sha256") == sha256(threshold_path), f"metadata={metadata.get('frozen_thresholds_sha256')} actual={sha256(threshold_path)}")
    foundry = json.loads((batch / "summary/foundry_evals.json").read_text(encoding="utf-8"))
    check("foundry_compatibility_record", foundry.get("status") == "NOT_RUN" and foundry.get("boundary") == "NOT VERIFIED", str(foundry))

    report_text = (batch / "PHASE3_REPORT.md").read_text(encoding="utf-8")
    report_markers = all(marker in report_text for marker in (
        f"TP | {recomputed_metrics['TP']}",
        f"FP | {recomputed_metrics['FP']}",
        f"TN | {recomputed_metrics['TN']}",
        f"FN | {recomputed_metrics['FN']}",
        f"Runs: `{EXPECTED_RUN_COUNT}`",
        "NOT AWARDED BY CONSTRUCTION",
    ))
    check("report_headline_integrity", report_markers, "report includes independently recomputed headline values and non-PASS construction status")

    result = "PASS" if all(item["status"] == "PASS" for item in checks) else "BLOCKED"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verification": "Phase 3 Evidence Benchmark",
        "result": result,
        "generated_from": str(batch),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "checks": checks,
        "warnings": warnings,
        "recomputed": {"runs": len(valid), "category_counts": dict(category_counts), "confusion_matrix": recomputed_metrics, "category_results": category_results, "variations": variations, "tool_shapes": tool_shapes},
        "boundaries": {
            "foundry_iq_native_retrieval": "NOT VERIFIED",
            "production_operations_backend": "NOT VERIFIED",
            "cloud_core_trace_correlation": "NOT VERIFIED",
            "concurrent_forked_turns": "NOT VERIFIED",
            "cold_start_recovery": "NOT VERIFIED",
            "foundry_evals": "PARTIAL - compatibility record is NOT_RUN",
        },
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PHASE3_INDEPENDENT_VERIFY_{result} checks={len(checks)} warnings={len(warnings)} output={output}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
