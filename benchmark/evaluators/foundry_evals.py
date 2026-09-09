"""Compatibility boundary for the optional Foundry Evals layer."""

from __future__ import annotations

from typing import Any


def evaluate_foundry_layer(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "NOT_RUN",
        "reason": "FoundryEvals was not invoked; this construction uses the deterministic LocalEvaluator.",
        "records_available": len(records),
        "evaluator_results": [],
        "boundary": "NOT VERIFIED",
    }
