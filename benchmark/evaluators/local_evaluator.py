"""Expected/actual evaluator for the deterministic local Phase 3 layer."""

from __future__ import annotations

from typing import Any


def evaluate_record(record: dict[str, Any]) -> dict[str, Any]:
    expected = record["expected"]
    actual = record.get("actual", {})
    mismatches: list[str] = []
    comparisons = {
        "should_trip": (expected["should_trip"], actual.get("trip")),
        "failure_type": (expected["expected_failure_type"], actual.get("failure_type")),
        "outcome": (expected["expected_outcome"], actual.get("outcome")),
        "useful_recheck": (expected["expected_useful_recheck"], actual.get("useful_recheck")),
        "healthy_completion": (expected["healthy_completion_expected"], actual.get("healthy_completion")),
    }
    for name, (want, got) in comparisons.items():
        if want != got:
            mismatches.append(f"{name}: expected={want!r} actual={got!r}")
    return {
        "valid": bool(record.get("valid", False)),
        "correct": bool(record.get("valid", False)) and not mismatches,
        "prediction_positive": bool(expected["should_trip"]),
        "actual_positive": bool(actual.get("trip")),
        "mismatches": mismatches,
        "category": record["category"],
        "scenario_id": record["scenario_id"],
    }
