"""Run the offline, deterministic subset of the Azure AI Evaluation SDK.

This runs the offline deterministic F1 evaluator on the already materialized
expected/actual classification labels. A separate bounded helper runs the
model-backed ToolCallAccuracy evaluator against the project's Azure deployment;
this script records that split without claiming a full hosted Foundry run.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from statistics import mean


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--normalized", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    from azure.ai.evaluation import F1ScoreEvaluator

    rows = [
        json.loads(line)
        for line in Path(args.normalized).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    evaluator = F1ScoreEvaluator(threshold=0.5)
    results = []
    for row in rows:
        expected = row["expected"].get("expected_failure_type") or "HEALTHY"
        actual = row["actual"].get("failure_type") or "HEALTHY"
        result = evaluator(response=actual, ground_truth=expected)
        results.append({
            "scenario_id": row["scenario_id"],
            "repetition": row["repetition"],
            "expected_label": expected,
            "actual_label": actual,
            "f1_score": result.get("f1_score"),
            "passed": result.get("f1_score_passed"),
            "status": result.get("f1_score_status"),
        })

    scores = [float(item["f1_score"]) for item in results]
    payload = {
        "status": "PARTIAL",
        "package": "azure-ai-evaluation",
        "package_version": importlib.metadata.version("azure-ai-evaluation"),
        "evaluator": "F1ScoreEvaluator",
        "evaluator_scope": "offline deterministic expected-vs-actual classification labels",
        "records": len(results),
        "completed": sum(item["status"] == "completed" for item in results),
        "passed": sum(bool(item["passed"]) for item in results),
        "mean_f1": mean(scores) if scores else None,
        "network": "DISABLED",
        "llm": "NOT INVOKED",
        "model_backed_trajectory_evaluators": "15-SCENARIO AGENTATHON PROFILE IS A SEPARATE OPTIONAL CLOUD EVALUATION - gpt-5-mini / australiaeast",
        "tool_call_accuracy": "SEE SEPARATE 15-SCENARIO COMPETITION ARTIFACT; no cloud result is implied by this offline evaluator",
        "boundary": "PARTIAL: offline SDK evaluator is complete and the model-backed run is execution-complete; cloud hosted Foundry evaluation orchestration remains NOT VERIFIED",
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FOUNDRY_EVAL_PARTIAL package=azure-ai-evaluation version={payload['package_version']} records={len(results)} passed={payload['passed']} output={output}")
    return 0 if payload["records"] > 0 and payload["completed"] == payload["records"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
