"""Controlled ON/OFF comparison metrics for the Phase 3 subset."""

from __future__ import annotations

from statistics import mean
from typing import Any


def compute(on_records: list[dict[str, Any]], off_records: list[dict[str, Any]]) -> dict[str, Any]:
    on = {(r["scenario_id"], r["repetition"]): r for r in on_records}
    off = {(r["scenario_id"], r["repetition"]): r for r in off_records}
    pairs = [(on[key], off[key]) for key in sorted(on.keys() & off.keys())]
    def avg(rows: list[dict[str, Any]], key: str) -> float | None:
        return mean(r["actual"][key] for r in rows) if rows else None
    return {
        "paired_runs": len(pairs),
        "fixture_control": "same scenario, repetition, prompt, tool arguments, world state, and local engine; only reasonfuse_enabled differs",
        "on": {"mean_tool_calls": avg([x[0] for x in pairs], "tool_calls"), "mean_steps": avg([x[0] for x in pairs], "steps")},
        "off": {"mean_tool_calls": avg([x[1] for x in pairs], "tool_calls"), "mean_steps": avg([x[1] for x in pairs], "steps")},
        "deltas_off_minus_on": {
            "mean_tool_calls": (avg([x[1] for x in pairs], "tool_calls") or 0) - (avg([x[0] for x in pairs], "tool_calls") or 0),
            "mean_steps": (avg([x[1] for x in pairs], "steps") or 0) - (avg([x[0] for x in pairs], "steps") or 0),
        },
    }
