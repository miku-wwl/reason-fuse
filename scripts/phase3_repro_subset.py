"""Re-run the Phase 3 representative subset and compare classifications."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_repo_root))
sys.path.insert(0, str(_repo_root / "src"))
from benchmark.runners.run_single import execute_scenario


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--raw", required=True)
    args = parser.parse_args()
    dataset = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    raw = [json.loads(line) for line in Path(args.raw).read_text(encoding="utf-8").splitlines() if line.strip()]
    baseline = {(row["scenario_id"], row["repetition"]): row for row in raw}
    selected = []
    for category in ("Healthy", "Exact Loop", "Oscillation", "Retrieval Churn", "Outcome Failure"):
        selected.extend([row for row in dataset if row["category"] == category][:2])
    failures = []
    for scenario in selected:
        expected = baseline[(scenario["scenario_id"], 1)]
        rerun = execute_scenario(scenario, 1, enabled=True, mode="REPRO")
        for field in ("trip", "failure_type", "outcome", "useful_recheck", "healthy_completion", "steps", "tool_calls", "side_effects"):
            if rerun["actual"].get(field) != expected["actual"].get(field):
                failures.append(f"{scenario['scenario_id']}:{field}:{rerun['actual'].get(field)!r}!={expected['actual'].get(field)!r}")
    if failures:
        print("PHASE3_REPRO_SUBSET_FAIL " + "; ".join(failures))
        return 1
    print(f"PHASE3_REPRO_SUBSET_PASS cases={len(selected)} categories=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
