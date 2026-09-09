"""Confusion matrix and bounded benchmark metrics."""

from __future__ import annotations

import math
from collections import Counter
from statistics import mean
from typing import Any, Iterable


def percentile(values: Iterable[float], p: float) -> float | None:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * p
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def compute(records: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [record for record in records if record.get("valid")]
    tp = sum(r["expected"]["should_trip"] and r["actual"]["trip"] for r in valid)
    tn = sum(not r["expected"]["should_trip"] and not r["actual"]["trip"] for r in valid)
    fp = sum(not r["expected"]["should_trip"] and r["actual"]["trip"] for r in valid)
    fn = sum(r["expected"]["should_trip"] and not r["actual"]["trip"] for r in valid)
    positive = tp + fn
    predicted_positive = tp + fp
    def ratio(numerator: int, denominator: int) -> float | None:
        return numerator / denominator if denominator else None
    precision = ratio(tp, predicted_positive)
    recall = ratio(tp, positive)
    f1 = (2 * precision * recall / (precision + recall)) if precision is not None and recall is not None and precision + recall else None
    by_category: dict[str, Any] = {}
    for category in sorted({r["category"] for r in valid}):
        rows = [r for r in valid if r["category"] == category]
        by_category[category] = {
            "runs": len(rows),
            "correct": sum(bool(r["evaluation"]["correct"]) for r in rows),
            "trip_rate": mean(bool(r["actual"]["trip"]) for r in rows),
            "expected_trip_rate": mean(bool(r["expected"]["should_trip"]) for r in rows),
            "failure_types": dict(Counter(r["actual"].get("failure_type") or "NONE" for r in rows)),
        }
    useful_expected = [r for r in valid if r["expected"]["expected_useful_recheck"]]
    outcome_failures = [r for r in valid if r["expected"]["expected_outcome"] == "POSTCONDITION_FAILED"]
    outcome_verified = [r for r in valid if r["expected"]["expected_outcome"] == "OUTCOME_VERIFIED"]
    return {
        "runs": len(records),
        "valid_runs": len(valid),
        "invalid_runs": len(records) - len(valid),
        "correct_runs": sum(bool(r["evaluation"]["correct"]) for r in valid),
        "confusion_matrix": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "metrics": {
            "accuracy": ratio(tp + tn, len(valid)),
            "precision": precision,
            "recall": recall,
            "false_positive_rate": ratio(fp, fp + tn),
            "false_negative_rate": ratio(fn, fn + tp),
            "f1": f1,
        },
        "latency_ms": {key: percentile((r["actual"]["containment_latency_ms"] for r in valid), value) for key, value in (("p50", .50), ("p95", .95), ("p99", .99))},
        "workload": {
            "mean_tool_calls": mean(r["actual"]["tool_calls"] for r in valid) if valid else None,
            "mean_steps": mean(r["actual"]["steps"] for r in valid) if valid else None,
            "mean_objective_progress_events": mean(r["actual"]["objective_progress_events"] for r in valid) if valid else None,
            "mean_redundant_tool_calls": mean(r["actual"]["redundant_tool_calls"] for r in valid) if valid else None,
        },
        "category_metrics": by_category,
        "outcome_failure_detection": {
            "runs": len(outcome_failures),
            "detected": sum(r["actual"].get("outcome") == "POSTCONDITION_FAILED" for r in outcome_failures),
        },
        "outcome_verification": {
            "runs": len(outcome_verified),
            "verified": sum(r["actual"].get("outcome") == "OUTCOME_VERIFIED" for r in outcome_verified),
        },
        "useful_recheck_preservation": {
            "runs": len(useful_expected),
            "preserved": sum(r["actual"].get("useful_recheck") is True for r in useful_expected),
        },
    }
