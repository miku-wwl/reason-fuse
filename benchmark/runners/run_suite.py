"""Run the complete deterministic Phase 3 suite and materialize evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark.datasets.validate_dataset import validate
from benchmark.evaluators.confusion_matrix import compute
from benchmark.evaluators.foundry_evals import evaluate_foundry_layer
from benchmark.evaluators.impact_metrics import compute as compute_impact
from benchmark.evaluators.local_evaluator import evaluate_record
from benchmark.runners.run_single import execute_scenario


def _json_default(value: Any) -> str:
    return str(value)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, default=_json_default) + "\n" for row in rows), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_suite(dataset_path: str | Path, output_dir: str | Path, repetitions: int = 1, include_impact: bool = False) -> dict[str, Any]:
    records = validate(dataset_path)
    output = Path(output_dir)
    if (output / "raw" / "runs.jsonl").exists():
        raise FileExistsError(f"raw evidence already exists; choose a new batch directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    raw: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    for repetition in range(1, repetitions + 1):
        for scenario in records:
            result = execute_scenario(scenario, repetition, enabled=True, mode="ON")
            raw.append(result)
            result["evaluation"] = evaluate_record(result)
            normalized.append(result)
    expected_runs = len(records) * repetitions
    if len(raw) != expected_runs:
        raise RuntimeError(f"suite run count mismatch: {len(raw)} != {expected_runs}")
    _write_jsonl(output / "raw" / "runs.jsonl", raw)
    _write_jsonl(output / "normalized" / "results.jsonl", normalized)
    metrics = compute(normalized)
    _write_json(output / "summary" / "metrics.json", metrics)
    _write_json(output / "summary" / "dataset_metadata.json", {
        "dataset": str(Path(dataset_path).as_posix()),
        "dataset_sha256": _sha256(Path(dataset_path)),
        "frozen_thresholds_path": "benchmark/datasets/frozen_thresholds.json",
        "frozen_thresholds_sha256": _sha256(Path("benchmark/datasets/frozen_thresholds.json")),
        "scenario_count": len(records),
        "repetitions": repetitions,
        "category_counts": dict(sorted(Counter(r["category"] for r in records).items())),
        "scenario_ids": [r["scenario_id"] for r in records],
        "fixture_scope": True,
    })
    foundry = evaluate_foundry_layer(normalized)
    _write_json(output / "summary" / "foundry_evals.json", foundry)
    impact: dict[str, Any] | None = None
    if include_impact:
        subset = records
        on = [execute_scenario(scenario, 1, enabled=True, mode="ON") for scenario in subset]
        off = [execute_scenario(scenario, 1, enabled=False, mode="OFF") for scenario in subset]
        for row in on + off:
            row["evaluation"] = evaluate_record(row)
        _write_jsonl(output / "raw" / "off_on.jsonl", on + off)
        impact = compute_impact(on, off)
        _write_json(output / "summary" / "off_on_impact.json", impact)
    manifest = {
        "phase": "Phase 3 Evidence Benchmark Construction",
        "batch": output.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command_scope": "local deterministic ReasonFuse engine; no network, LLM, Azure, or hosted Operations backend",
        "dataset_path": str(Path(dataset_path).as_posix()),
        "dataset_sha256": _sha256(Path(dataset_path)),
        "expected_runs": expected_runs,
        "actual_runs": len(normalized),
        "valid_runs": sum(bool(row.get("valid")) for row in normalized),
        "invalid_runs": sum(not bool(row.get("valid")) for row in normalized),
        "correct_runs": sum(bool(row["evaluation"]["correct"]) for row in normalized),
        "repetitions": repetitions,
        "impact_subset": impact,
        "source": {"git_commit": normalized[0]["source_manifest"]["git_commit"] if normalized else "NOT AVAILABLE"},
        "boundaries": [
            "Foundry IQ native retrieval: NOT VERIFIED",
            "production Operations backend: NOT VERIFIED",
            "cloud Core trace correlation: NOT VERIFIED",
            "concurrent/forked turns and cold-start recovery: NOT VERIFIED",
        ],
    }
    _write_json(output / "manifest.json", manifest)
    print(f"PHASE3_SUITE_COMPLETE runs={len(normalized)} valid={manifest['valid_runs']} correct={manifest['correct_runs']} output={output}")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="benchmark/datasets/reasonfuse_v2.jsonl")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--include-impact", action="store_true")
    args = parser.parse_args(argv)
    try:
        run_suite(args.dataset, args.output_dir, args.repetitions, args.include_impact)
    except Exception as exc:
        print(f"PHASE3_SUITE_FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
