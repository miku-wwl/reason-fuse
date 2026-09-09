"""Run a bounded model-backed Foundry ToolCallAccuracy evaluation subset.

The project deployment is configured in Azure as ``gpt-5-mini`` in
``australiaeast``. This script uses the current ``AZURE_OPENAI_ENDPOINT``
environment value and Azure CLI credential without printing either endpoint or
credential material. It intentionally evaluates the 15-scenario Agentathon
profile instead of silently expanding the cloud bill with repeated runs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def _tool_definition(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    body = arguments.get("body", arguments)
    properties = {
        str(key): {"type": "string"}
        for key in body
        if isinstance(body, dict)
    }
    return {
        "name": tool_name,
        "description": f"Deterministic ReasonFuse fixture operation {tool_name}.",
        "parameters": {"type": "object", "properties": properties},
    }


def _tool_call(tool_name: str, arguments: dict[str, Any], call_index: int) -> dict[str, Any]:
    body = arguments.get("body", arguments)
    return {
        "type": "tool_call",
        "name": tool_name,
        "tool_call_id": f"phase3-tool-call-{call_index:03d}",
        "arguments": body,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--per-category", type=int, default=3)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--scenario-id", action="append", dest="scenario_ids",
                        help="Evaluate only the named scenario IDs; repeat for multiple IDs.")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--transport", choices=("evaluator_async", "direct_azure_openai"), default="evaluator_async")
    args = parser.parse_args()

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5-mini")
    if not endpoint:
        raise SystemExit("FOUNDRY_TOOLCALL_CONFIG_ERROR AZURE_OPENAI_ENDPOINT is missing")

    from azure.ai.evaluation import ToolCallAccuracyEvaluator
    from azure.ai.evaluation._legacy.prompty._utils import prepare_open_ai_request_params
    from azure.identity import AzureCliCredential
    from azure.identity import get_bearer_token_provider
    from openai import AzureOpenAI

    dataset = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    raw = [json.loads(line) for line in Path(args.raw).read_text(encoding="utf-8").splitlines() if line.strip()]
    raw_by_key = {(row["scenario_id"], row["repetition"]): row for row in raw}
    selected = []
    for category in ("Healthy", "Exact Loop", "Oscillation", "Retrieval Churn", "Outcome Failure"):
        selected.extend([row for row in dataset if row["category"] == category][: args.per_category])

    model_config = {
        "type": "azure_openai",
        "azure_endpoint": endpoint,
        "azure_deployment": deployment,
    }
    max_completion_tokens = int(os.environ.get("REASONFUSE_TOOLCALL_MAX_COMPLETION_TOKENS", "8192"))
    selected_pairs = [
        (scenario, raw_by_key[(scenario["scenario_id"], repetition)])
        for scenario in selected
        for repetition in range(1, args.repetitions + 1)
    ]
    if args.scenario_ids:
        wanted = set(args.scenario_ids)
        selected_pairs = [pair for pair in selected_pairs if pair[0]["scenario_id"] in wanted]

    thread_local = threading.local()

    def evaluator_for_thread():
        evaluator = getattr(thread_local, "evaluator", None)
        if evaluator is None:
            evaluator = ToolCallAccuracyEvaluator(
                model_config=model_config,
                threshold=3,
                credential=AzureCliCredential(process_timeout=60),
                # gpt-5-mini is a reasoning model. The evaluation SDK then replaces
                # legacy max_tokens with max_completion_tokens before the Azure call.
                is_reasoning_model=True,
            )
            # The SDK's reasoning-model default is 60,000 completion tokens,
            # which is excessive for this evaluator's short JSON score and
            # makes the competition run unnecessarily slow. Keep a bounded but
            # ample reasoning budget for the evaluation-only model calls.
            evaluator._flow._model.parameters["max_completion_tokens"] = max_completion_tokens
            thread_local.evaluator = evaluator
        return evaluator

    def client_for_thread():
        client = getattr(thread_local, "client", None)
        if client is None:
            credential = AzureCliCredential(process_timeout=60)
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment,
                api_version="2024-02-15-preview",
                azure_ad_token_provider=token_provider,
                max_retries=3,
                default_headers={"User-Agent": "reasonfuse-phase3-toolcall-accuracy"},
            )
            thread_local.client = client
        return client

    def evaluate(pair):
        scenario, raw_row = pair
        calls = []
        definitions_by_name: dict[str, dict[str, Any]] = {}
        for call_index, event in enumerate(raw_row.get("raw_events", []), 1):
            if not event.get("executed"):
                continue
            action = scenario["actions"][event["step"] - 1]
            name = action["tool_name"]
            calls.append(_tool_call(name, action["arguments"], call_index))
            definitions_by_name[name] = _tool_definition(name, action["arguments"])
        try:
            evaluator = evaluator_for_thread()
            if args.transport == "evaluator_async":
                # The SDK's public sync wrapper starts a worker event loop. On
                # this Windows/Python environment that wrapper intermittently
                # loses the Azure connection, while the evaluator's own async
                # path succeeds with the same validated input and model request.
                evaluation = asyncio.run(evaluator._real_call(
                    query=scenario["user_prompt"],
                    tool_calls=calls,
                    tool_definitions=list(definitions_by_name.values()),
                ))
            else:
                raw_input = {
                    "query": scenario["user_prompt"],
                    "tool_calls": calls,
                    "tool_definitions": list(definitions_by_name.values()),
                }
                evaluator._validator.validate_eval_input(raw_input)
                eval_input = evaluator._convert_kwargs_to_eval_input(**raw_input)
                if isinstance(eval_input, dict) and eval_input.get("error_message"):
                    raise RuntimeError(eval_input["error_message"])
                flow = evaluator._flow
                messages = flow.render(**eval_input)
                params = prepare_open_ai_request_params(flow._model, messages)
                params["max_completion_tokens"] = max_completion_tokens
                response = client_for_thread().chat.completions.create(**params)
                content = response.choices[0].message.content or ""
                llm_output = json.loads(content)
                score = float(llm_output["score"])
                if score < 1 or score > 5:
                    raise ValueError(f"Tool call accuracy score outside [1,5]: {score}")
                evaluation = {
                    "tool_call_accuracy": score,
                    "tool_call_accuracy_score": score,
                    "tool_call_accuracy_result": "pass" if score >= 3 else "fail",
                    "tool_call_accuracy_passed": score >= 3,
                    "tool_call_accuracy_reason": llm_output.get("reason", ""),
                    "tool_call_accuracy_status": "completed",
                    "tool_call_accuracy_threshold": 3,
                    "tool_call_accuracy_properties": {
                        "transport": "direct_azure_openai",
                        "model": response.model,
                        "finish_reason": response.choices[0].finish_reason,
                    },
                }
            return {
                "scenario_id": scenario["scenario_id"],
                "category": scenario["category"],
                "repetition": raw_row["repetition"],
                "status": evaluation.get("tool_call_accuracy_status", "completed"),
                "score": evaluation.get("tool_call_accuracy_score"),
                "passed": evaluation.get("tool_call_accuracy_passed"),
                "result": evaluation.get("tool_call_accuracy_result"),
                "error_message": evaluation.get("error_message"),
                "tool_calls": len(calls),
            }
        except Exception as exc:  # preserve exact evaluator failure per case
            return {
                "scenario_id": scenario["scenario_id"],
                "category": scenario["category"],
                "repetition": raw_row["repetition"],
                "status": "ERROR",
                "score": None,
                "passed": False,
                "result": None,
                "error_message": f"{type(exc).__name__}: {exc}",
                "tool_calls": len(calls),
            }

    workers = max(1, min(args.workers, len(selected_pairs)))
    if workers == 1:
        results = [evaluate(pair) for pair in selected_pairs]
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="toolcall-eval") as pool:
            results = list(pool.map(evaluate, selected_pairs))

    completed = [row for row in results if row["status"] == "completed"]
    errors = [row for row in results if row["status"] == "ERROR" or row.get("error_message")]
    threshold_passed = sum(bool(row.get("passed")) for row in results)
    expected_cases = len(selected_pairs)
    payload = {
        "status": "PASS" if len(results) == expected_cases and not errors else "PARTIAL",
        "evaluator": "ToolCallAccuracyEvaluator",
        "package": "azure-ai-evaluation",
        "deployment": deployment,
        "region": "australiaeast",
        "subset_size": len(results),
        "per_category": args.per_category,
        "repetitions": args.repetitions,
        "workers": workers,
        "completed": len(completed),
        "errors": len(errors),
        "threshold_passed": threshold_passed,
        "threshold": 3,
        "max_completion_tokens": max_completion_tokens,
        "network": "AZURE_OPENAI_MODEL_CALLS",
        "llm": "INVOKED",
        "competition_15_scenario_run": "RUN" if len(results) == 15 and args.repetitions == 1 else "NOT RUN - bounded or repeated subset",
        "transport": args.transport,
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FOUNDRY_TOOLCALL_ACCURACY_{payload['status']} deployment={deployment} region=australiaeast subset={len(results)} completed={len(completed)} errors={len(errors)} output={output}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
