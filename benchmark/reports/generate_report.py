"""Render a concise, evidence-linked Phase 3 construction report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _value(value: Any) -> str:
    if value is None:
        return "NOT AVAILABLE"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def render(run_dir: str | Path, output: str | Path | None = None) -> Path:
    run = Path(run_dir)
    manifest = _load(run / "manifest.json")
    metrics = _load(run / "summary" / "metrics.json")
    dataset_metadata = _load(run / "summary" / "dataset_metadata.json")
    foundry = _load(run / "summary" / "foundry_evals.json")
    micro_path = run / "microbenchmark.json"
    micro = _load(micro_path) if micro_path.exists() else None
    matrix = metrics["confusion_matrix"]
    overall = metrics["metrics"]
    lines = [
        "# Phase 3 Evidence Benchmark — Construction Report",
        "",
        "> This is a construction-layer report. It records executed local evidence; it does not self-award the independent Phase 3 verification result.",
        "",
        "## Scope and result",
        "",
        f"- Batch: `{manifest['batch']}`",
        f"- Dataset: `{manifest['scenario_path'] if 'scenario_path' in manifest else manifest['dataset_path']}`",
        f"- Dataset SHA-256: `{manifest['dataset_sha256']}`",
        f"- Frozen thresholds SHA-256: `{dataset_metadata['frozen_thresholds_sha256']}`.",
        f"- Runs: `{manifest['actual_runs']}` / expected `{manifest['expected_runs']}`",
        f"- Valid runner records: `{manifest['valid_runs']}`; invalid: `{manifest['invalid_runs']}`",
        f"- LocalEvaluator-correct records: `{manifest['correct_runs']}`",
        f"- Execution layer: `{manifest['command_scope']}`",
        "",
        "Construction status: `COMPLETE — local deterministic evidence materialized`.",
        "Independent verification status: `NOT RUN by this construction command`.",
        "",
        "## Confusion matrix and overall metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| TP | {matrix['TP']} |",
        f"| FP | {matrix['FP']} |",
        f"| TN | {matrix['TN']} |",
        f"| FN | {matrix['FN']} |",
        f"| Recall | {_value(overall['recall'])} |",
        f"| Precision | {_value(overall['precision'])} |",
        f"| FPR | {_value(overall['false_positive_rate'])} |",
        f"| FNR | {_value(overall['false_negative_rate'])} |",
        f"| Accuracy | {_value(overall['accuracy'])} |",
        f"| F1 | {_value(overall['f1'])} |",
        "",
        "## Category metrics",
        "",
        "| Category | Runs | Correct | Expected trip rate | Actual trip rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for category, item in metrics["category_metrics"].items():
        lines.append(f"| {category} | {item['runs']} | {item['correct']} | {_value(item['expected_trip_rate'])} | {_value(item['trip_rate'])} |")
    lines.extend([
        "",
        f"- Postcondition failure detection: `{metrics['outcome_failure_detection']['detected']}/{metrics['outcome_failure_detection']['runs']}`.",
        f"- Successful postcondition verification: `{metrics['outcome_verification']['verified']}/{metrics['outcome_verification']['runs']}`.",
        f"- Useful recheck preservation: `{metrics['useful_recheck_preservation']['preserved']}/{metrics['useful_recheck_preservation']['runs']}`.",
        "",
        "## Work and latency",
        "",
        f"- Tool calls/run: `{_value(metrics['workload']['mean_tool_calls'])}`.",
        f"- Redundant canonical calls/run: `{_value(metrics['workload']['mean_redundant_tool_calls'])}`.",
        f"- Steps/run: `{_value(metrics['workload']['mean_steps'])}`.",
        f"- Containment latency p50/p95/p99 ms: `{_value(metrics['latency_ms']['p50'])}` / `{_value(metrics['latency_ms']['p95'])}` / `{_value(metrics['latency_ms']['p99'])}`.",
        "- Tokens/run: `NOT AVAILABLE` (no LLM was invoked).",
        "- Cost/run: `NOT AVAILABLE` (no billable provider was invoked).",
        "",
        "## Controlled OFF/ON subset",
        "",
    ])
    impact_path = run / "summary" / "off_on_impact.json"
    if impact_path.exists():
        impact = _load(impact_path)
        lines.extend([
            f"- Paired runs: `{impact['paired_runs']}`.",
            f"- ON mean tool calls / steps: `{_value(impact['on']['mean_tool_calls'])}` / `{_value(impact['on']['mean_steps'])}`.",
            f"- OFF mean tool calls / steps: `{_value(impact['off']['mean_tool_calls'])}` / `{_value(impact['off']['mean_steps'])}`.",
            f"- OFF-minus-ON mean tool calls / steps: `{_value(impact['deltas_off_minus_on']['mean_tool_calls'])}` / `{_value(impact['deltas_off_minus_on']['mean_steps'])}`.",
            f"- Control definition: {impact['fixture_control']}.",
        ])
    else:
        lines.append("- `NOT RUN`.")
    lines.extend(["", "## Microbenchmark"])
    if micro:
        lines.extend([
            "",
            f"- Status: `{micro['status']}`; events: `{micro['events']}`.",
            f"- Events/second: `{_value(micro['events_per_second'])}`.",
            f"- Per-event latency p50/p95/p99 ns: `{_value(micro['per_event_latency_ns']['p50'])}` / `{_value(micro['per_event_latency_ns']['p95'])}` / `{_value(micro['per_event_latency_ns']['p99'])}`.",
            f"- Peak traced memory: `{micro['peak_traced_memory_bytes']}` bytes.",
        ])
    else:
        lines.append("\n- `NOT RUN`.")
    lines.extend([
        "",
        "## Evidence and boundaries",
        "",
        "Raw evidence is in `raw/runs.jsonl`; normalized records are in `normalized/results.jsonl`; machine summaries are in `summary/`.",
        "",
        f"- FoundryEvals layer: `{foundry['status']}` — {foundry['reason']}",
        "- Foundry IQ native retrieval: `NOT VERIFIED`.",
        "- Production Operations backend: `NOT VERIFIED`.",
        "- Cloud Core trace correlation: `NOT VERIFIED`.",
        "- Concurrent/forked turns and cold-start recovery: `NOT VERIFIED`.",
        "- Fixture reset: deterministic local reset is recorded per run; hosted/production isolation is not claimed.",
        "- Architecture change required by this local construction: `NO`.",
        "",
        "## Phase 3 Result",
        "",
        "`NOT AWARDED BY CONSTRUCTION — READY FOR INDEPENDENT VALIDATION`.",
        "",
        "## Reproduction",
        "",
        "```powershell",
        "$env:PYTHONPATH = 'src'",
        ".venv/Scripts/python.exe -m benchmark.datasets.validate_dataset",
        ".venv/Scripts/python.exe -m benchmark.runners.run_suite --dataset benchmark/datasets/reasonfuse_v2.jsonl --output-dir <run-dir> --repetitions 3 --include-impact",
        ".venv/Scripts/python.exe -m benchmark.microbenchmark.run_microbenchmark --output <run-dir>/microbenchmark.json",
        "```",
        "",
        f"Source commit recorded by runner: `{manifest['source']['git_commit']}`.",
    ])
    destination = Path(output) if output else run / "PHASE3_REPORT.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PHASE3_REPORT_WRITTEN path={destination}")
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    render(args.run_dir, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
