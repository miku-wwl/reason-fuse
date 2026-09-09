"""Portable validation for the deterministic Phase 3 dataset."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


CATEGORIES = ("Healthy", "Exact Loop", "Oscillation", "Retrieval Churn", "Outcome Failure")
ID_RE = re.compile(r"^(H|EL|OS|RC|OF)-\d{3}$")
REQUIRED_EXPECTED = {
    "should_trip", "expected_failure_type", "expected_outcome",
    "expected_useful_recheck", "healthy_completion_expected",
}
REQUIRED_ACTION = {"type", "tool_name", "arguments", "result", "side_effect", "approved"}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    if not source.exists():
        raise FileNotFoundError(source)
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            _fail(errors, f"line {line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            _fail(errors, f"line {line_number}: record is not an object")
            continue
        records.append(value)
        scenario_id = value.get("scenario_id")
        category = value.get("category")
        if not isinstance(scenario_id, str) or not ID_RE.fullmatch(scenario_id):
            _fail(errors, f"line {line_number}: invalid scenario_id={scenario_id!r}")
        if category not in CATEGORIES:
            _fail(errors, f"line {line_number}: invalid category={category!r}")
        elif scenario_id and not scenario_id.startswith({"Healthy": "H", "Exact Loop": "EL", "Oscillation": "OS", "Retrieval Churn": "RC", "Outcome Failure": "OF"}[category]):
            _fail(errors, f"line {line_number}: category/id prefix mismatch")
        for field in ("scenario_version", "description", "user_prompt", "run_contract_version",
                      "toolbox_version", "knowledge_base_version", "agent_version", "model_version"):
            if not isinstance(value.get(field), str) or not value[field]:
                _fail(errors, f"line {line_number}: missing string field {field}")
        if not isinstance(value.get("initial_world_state"), dict):
            _fail(errors, f"line {line_number}: initial_world_state must be an object")
        if not isinstance(value.get("fault_configuration"), dict):
            _fail(errors, f"line {line_number}: fault_configuration must be an object")
        expected = value.get("expected")
        if not isinstance(expected, dict) or not REQUIRED_EXPECTED <= set(expected):
            _fail(errors, f"line {line_number}: expected fields incomplete")
        else:
            if not isinstance(expected["should_trip"], bool) or not isinstance(expected["expected_useful_recheck"], bool) or not isinstance(expected["healthy_completion_expected"], bool):
                _fail(errors, f"line {line_number}: expected booleans invalid")
        actions = value.get("actions")
        if not isinstance(actions, list) or not actions:
            _fail(errors, f"line {line_number}: actions must be non-empty")
        else:
            for action_index, action in enumerate(actions):
                if not isinstance(action, dict) or not REQUIRED_ACTION <= set(action):
                    _fail(errors, f"line {line_number}: action {action_index} incomplete")
                    continue
                if not isinstance(action["tool_name"], str) or not isinstance(action["arguments"], dict) or not isinstance(action["result"], dict):
                    _fail(errors, f"line {line_number}: action {action_index} types invalid")
                if not isinstance(action["side_effect"], bool) or not isinstance(action["approved"], bool):
                    _fail(errors, f"line {line_number}: action {action_index} flags invalid")
    ids = [r.get("scenario_id") for r in records]
    if len(records) != 100:
        _fail(errors, f"expected 100 records, got {len(records)}")
    if len(set(ids)) != len(ids):
        _fail(errors, "scenario IDs are not unique")
    for category in CATEGORIES:
        count = sum(r.get("category") == category for r in records)
        if count != 20:
            _fail(errors, f"category {category!r}: expected 20, got {count}")
    return records if not errors else (_raise(errors))


def _raise(errors: list[str]) -> list[dict[str, Any]]:
    raise ValueError("dataset validation failed:\n" + "\n".join(errors))


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(Path(__file__).with_name("reasonfuse_v1.jsonl")))
    args = parser.parse_args(argv)
    try:
        records = validate(args.dataset)
    except Exception as exc:  # CLI must return a useful failure without a traceback flood.
        print(f"DATASET_VALIDATION_FAIL {exc}", file=sys.stderr)
        return 1
    counts = {category: sum(r["category"] == category for r in records) for category in CATEGORIES}
    print(f"DATASET_VALIDATION_PASS scenarios={len(records)} counts={counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
