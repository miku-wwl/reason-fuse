"""Deterministic, offline scenario reset used by the Phase 3 fixture runner."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def reset_scenario(scenario: dict[str, Any], repetition: int, mode: str) -> dict[str, Any]:
    seed = f"{scenario['scenario_id']}|{repetition}|{mode}|{scenario['scenario_version']}".encode()
    epoch = hashlib.sha256(seed).hexdigest()[:16]
    return {
        "reset": "RESET_COMPLETE",
        "fixture_scope": True,
        "network": "DISABLED",
        "epoch": epoch,
        "conversation_id": f"conv-benchmark-{epoch}",
        "counters": {"steps": 0, "tool_calls": 0, "side_effects": 0},
        "world_state": scenario.get("initial_world_state", {}),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario_id")
    parser.add_argument("--repetition", type=int, default=1)
    parser.add_argument("--mode", default="ON")
    args = parser.parse_args()
    scenario = {"scenario_id": args.scenario_id, "scenario_version": "reasonfuse-v1", "initial_world_state": {}}
    print(json.dumps(reset_scenario(scenario, args.repetition, args.mode), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
