"""Run the required 10,000-event local ReasonFuse microbenchmark."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark.evaluators.confusion_matrix import percentile
from reasonfuse.core.contract import RunContract
from reasonfuse.core.engine import ReasonFuseEngine
from reasonfuse.core.state import ReasonFuseState


EVENTS = 10_000


def _engine(packet: int) -> ReasonFuseEngine:
    contract = RunContract(max_steps=100, max_tool_calls=100, max_stalled_steps=100,
                           max_oscillation_cycles=2, max_retrieval_churn=3,
                           max_side_effects=10, required_objective_progress_interval=100)
    state = ReasonFuseState(run_id=f"micro-{packet:04d}", contract_limits=contract.to_dict(), reasonfuse_enabled=True)
    return ReasonFuseEngine(state, contract)


def _event(packet: int, index: int) -> tuple[str, dict[str, Any], dict[str, Any], bool]:
    kind = packet % 5
    if kind == 0:
        return "config_check", {"body": {"service_name": "orders"}}, {"status": "INCONCLUSIVE", "evidence_keys": []}, False
    if kind == 1:
        name = "service_status" if index % 2 == 0 else "database_health"
        return name, {"body": {"service_name": "orders"}}, {"status": "INCONCLUSIVE", "evidence_keys": []}, False
    if kind == 2:
        return "retrieval_search", {"body": {"query": f"equivalent wording {index}"}}, {
            "query": f"equivalent wording {index}",
            "retrieval": {"source_keys": ["src-micro"], "chunk_ids": ["chunk-micro"], "citation_ids": ["cit-micro"], "content_hashes": ["hash-micro"], "knowledge_base_version": "fixture-kb-v1"},
            "evidence_keys": ["retrieval:src-micro"],
        }, False
    if kind == 3:
        return "restart_service", {"body": {"service_name": "orders"}}, {"accepted": True, "generation": f"g-{packet}"}, True
    return "read_runtime_state", {"body": {}}, {"status": "INCONCLUSIVE", "evidence_keys": []}, False


def run(output: str | Path) -> dict[str, Any]:
    timings_ns: list[int] = []
    decisions: Counter[str] = Counter()
    fuse_reasons: Counter[str] = Counter()
    packets = EVENTS // 10
    tracemalloc.start()
    wall_start = time.perf_counter_ns()
    event_count = 0
    for packet in range(packets):
        engine = _engine(packet)
        for index in range(10):
            tool_name, arguments, result, side_effect = _event(packet, index)
            started = time.perf_counter_ns()
            decision = engine.before_dispatch(tool_name, arguments)
            if decision.allow:
                engine.record(tool_name, arguments, result, executed=True, side_effect=side_effect, approved=True)
                decisions["ALLOW"] += 1
            else:
                decisions[decision.reason or "BLOCK"] += 1
            elapsed = time.perf_counter_ns() - started
            timings_ns.append(elapsed)
            event_count += 1
            if engine.state.fuse_reason:
                fuse_reasons[engine.state.fuse_reason] += 1
        # The synthetic outcome packet intentionally exercises a bounded
        # accepted side-effect path; this benchmark measures core decisions,
        # not an external observer.
    wall_ns = time.perf_counter_ns() - wall_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = {
        "status": "PASS" if event_count == EVENTS else "FAIL",
        "events": event_count,
        "packets": packets,
        "fixture_scope": True,
        "network": "DISABLED",
        "llm": "NOT INVOKED",
        "wall_time_ms": wall_ns / 1_000_000,
        "events_per_second": event_count / (wall_ns / 1_000_000_000) if wall_ns else None,
        "per_event_latency_ns": {"p50": percentile(timings_ns, .50), "p95": percentile(timings_ns, .95), "p99": percentile(timings_ns, .99), "mean": statistics.mean(timings_ns)},
        "peak_traced_memory_bytes": peak_bytes,
        "decision_counts": dict(decisions),
        "fuse_reason_observations": dict(fuse_reasons),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "boundary": "local deterministic core only; not a production throughput or hosted latency claim",
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"MICROBENCHMARK_PASS events={event_count} output={path}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = run(args.output)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
