"""Run the bounded Phase 4 clean-start sequence against the fresh environment.

The script combines the four deterministic Judge Mode demos with the hosted
APIM/Operations, affinity, SSE, candidate-regression, and rollback checks. It
does not run a large benchmark; it exercises one bounded instance of each
Phase 4 gate and records which evidence layer each result belongs to.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from azure.identity import AzureCliCredential

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.phase4_production_story import run_phase4  # noqa: E402
from scripts.support.validation import Evidence, HostedClient, Operations, output_text, runtime_state, safe_headers  # noqa: E402


def role_of(response: dict[str, Any]) -> str:
    name = (response.get("agent_reference") or {}).get("name", "")
    if name.endswith("-candidate"):
        return "candidate"
    if name.endswith("-stable"):
        return "stable"
    return "UNKNOWN"


def function_names(response: dict[str, Any]) -> list[str]:
    return [item.get("name", "") for item in response.get("output", []) if item.get("type") == "function_call"]


def release_snapshot(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": role_of(response),
        "agent_reference": response.get("agent_reference"),
        "agent_session_id": response.get("agent_session_id"),
        "conversation_id": (response.get("conversation") or {}).get("id"),
        "function_names": function_names(response),
        "response_id": response.get("response_id") or response.get("id"),
    }


def direct_client(evidence: Evidence, role: str) -> HostedClient:
    project = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
    endpoint = f"{project}/agents/reasonfuse-phase1-{role}/endpoint/protocols/openai"
    return HostedClient(evidence, base_url=endpoint)


def bounded_client(evidence: Evidence, base_url: str) -> HostedClient:
    client = HostedClient(evidence, base_url=base_url)
    client.http.close()
    client.http = httpx.Client(timeout=httpx.Timeout(150, connect=20))
    return client


def hosted_operations(evidence: Evidence) -> dict[str, Any]:
    operations = Operations(evidence)
    operations.reset()
    client = bounded_client(evidence, os.environ["APIM_ENDPOINT"])
    try:
        conversation = client.conversation()
        response = client.turn(
            "Call the dns_resolution tool exactly once for hostname api.reasonfuse.local.",
            conversation=conversation,
        )
        names = function_names(response)
        counts = operations.snapshot()["counts"]
        assert counts.get("dns_resolution:api.reasonfuse.local", 0) == 1
        assert not any(key.startswith("restart_service:") for key in counts)
        state_response = client.turn("Call read_runtime_state and return its JSON.", conversation=conversation)
        state = runtime_state(state_response)
        snapshot = release_snapshot(response)
        evidence.write("HOSTED_OPERATION_SCENARIO", **snapshot, runtime_state=state)
        return {"status": "PASS", "scenario": "hosted_operations", **snapshot, "runtime_state": state,
                "external_counts": counts}
    finally:
        client.close()


def hosted_affinity_and_fresh(evidence: Evidence) -> dict[str, Any]:
    operations = Operations(evidence)
    operations.reset()
    persistent = bounded_client(evidence, os.environ["APIM_ENDPOINT"])
    try:
        conversation = persistent.conversation()
        first = persistent.turn(
            "Call dns_resolution exactly once for api.reasonfuse.local.", conversation=conversation,
        )
        second = persistent.turn(
            "Call service_status exactly once for orders.", conversation=conversation,
        )
        counts = operations.snapshot()["counts"]
        assert counts.get("dns_resolution:api.reasonfuse.local", 0) >= 1
        assert counts.get("service_status:orders", 0) >= 1
        assert not any(key.startswith("restart_service:") for key in counts)
        first_snapshot = release_snapshot(first)
        second_snapshot = release_snapshot(second)
        sticky = first_snapshot["role"] == second_snapshot["role"] and first_snapshot["role"] != "UNKNOWN"
        fresh_client = bounded_client(evidence, os.environ["APIM_ENDPOINT"])
        try:
            fresh_conversation = fresh_client.conversation()
            fresh = fresh_client.turn("Call read_runtime_state and return its JSON.", conversation=fresh_conversation)
            fresh_snapshot = release_snapshot(fresh)
        finally:
            fresh_client.close()
        result = {
            "status": "PASS" if sticky else "FAIL",
            "persistent": {"conversation_id": conversation, "first": first_snapshot, "second": second_snapshot, "sticky": sticky},
            "fresh": {"conversation_id": fresh_conversation, **fresh_snapshot},
            "external_counts": counts,
            "scope": "real APIM responses and persistent HTTP client cookie jar",
        }
        evidence.write("APIM_AFFINITY", **result)
        return result
    finally:
        persistent.close()


def hosted_sse(evidence: Evidence) -> dict[str, Any]:
    operations = Operations(evidence)
    operations.reset()
    client = bounded_client(evidence, os.environ["APIM_ENDPOINT"])
    try:
        conversation = client.conversation()
        body = {
            "input": "Reply with the word PASS and no tool call.",
            "stream": True,
            "store": True,
            "conversation": conversation,
        }
        started = time.perf_counter()
        chunks: list[dict[str, Any]] = []
        with client.http.stream("POST", client.base + "/responses", params={"api-version": "v1"},
                                json=body, headers=client.headers(), timeout=180) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunks.append({"received_ms": round((time.perf_counter() - started) * 1000, 3), "line": line[:500]})
        final_ms = round((time.perf_counter() - started) * 1000, 3)
        incremental = len(chunks) >= 2 and chunks[0]["received_ms"] < final_ms
        result = {
            "status": "PASS" if incremental else "PARTIAL",
            "conversation_id": conversation,
            "chunk_count": len(chunks),
            "first_chunk_ms": chunks[0]["received_ms"] if chunks else None,
            "final_completion_ms": final_ms,
            "incremental_arrival": incremental,
            "headers": safe_headers(response.headers),
        }
        evidence.write("APIM_SSE", **result, chunks=chunks[:20])
        return result
    finally:
        client.close()


def candidate_regression(evidence: Evidence) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for role in ("stable", "candidate"):
        operations = Operations(evidence)
        operations.reset()
        client = direct_client(evidence, role)
        try:
            conversation = client.conversation()
            response = client.turn(
                "This is the explicitly named Phase 4 candidate regression probe. Use the tools now; "
                "do not answer with a recommendation after the first result. Call dns_resolution exactly "
                "once for api.orders.reasonfuse.local. If the result is INCONCLUSIVE, Stable must call "
                "service_status exactly once, while Candidate must repeat dns_resolution until ReasonFuse "
                "contains the no-progress loop. Follow the release's seeded behavior.",
                conversation=conversation,
            )
            names = function_names(response)
            state_response = client.turn("Call read_runtime_state and return its JSON.", conversation=conversation)
            state = runtime_state(state_response)
            snapshot = release_snapshot(response)
            actual_counts = operations.snapshot()["counts"]
            results[role] = {
                "status": "PASS",
                **snapshot,
                "runtime_state": state,
                "operation_counts": actual_counts,
                "answer_excerpt": output_text(response)[:500],
            }
            evidence.write("CANDIDATE_REGRESSION", **results[role])
        finally:
            client.close()
    stable_names = results["stable"]["function_names"]
    candidate_names = results["candidate"]["function_names"]
    stable_good = "operations___dns_resolution" in stable_names and "operations___service_status" in stable_names
    candidate_dns_count = candidate_names.count("operations___dns_resolution")
    candidate_good = candidate_dns_count >= 2 and "operations___service_status" not in candidate_names
    result = {
        "status": "PASS" if stable_good and candidate_good else "FAIL",
        "stable": results["stable"],
        "candidate": results["candidate"],
        "causality": "RELEASE_ROLE-specific Phase 4 instruction; ReasonFuse middleware remains shared",
    }
    evidence.write("CANDIDATE_REGRESSION_ASSERTIONS", **result)
    return result


def apim_pool(evidence: Evidence, candidate_weight: int, stable_weight: int) -> dict[str, Any]:
    credential = AzureCliCredential(process_timeout=60)
    try:
        subscription = os.environ["AZURE_SUBSCRIPTION_ID"]
        rg = os.environ["AZURE_RESOURCE_GROUP"]
        apim = os.environ["APIM_NAME"]
        base = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.ApiManagement/service/{apim}/backends"
        headers = {"Authorization": f"Bearer {credential.get_token('https://management.azure.com/.default').token}"}
        api_version = "2025-03-01-preview"
        stable_id = httpx.get(f"{base}/stable?api-version={api_version}", headers=headers, timeout=60).json()["id"]
        candidate_id = httpx.get(f"{base}/candidate?api-version={api_version}", headers=headers, timeout=60).json()["id"]
        pool_url = f"{base}/reasonfuse-canary?api-version={api_version}"
        body = {
            "properties": {
                "type": "Pool",
                "pool": {
                    "services": [
                        {"id": stable_id, "priority": 1, "weight": stable_weight},
                        {"id": candidate_id, "priority": 1, "weight": candidate_weight},
                    ],
                    "sessionAffinity": {"sessionId": {"source": "cookie", "name": "ReasonFuseAffinity"}},
                },
            }
        }
        response = httpx.put(pool_url, headers={**headers, "Content-Type": "application/json"}, json=body, timeout=120)
        response.raise_for_status()
        evidence.write("APIM_POOL_UPDATE", stable_weight=stable_weight, candidate_weight=candidate_weight, status_code=response.status_code)
        return {"status": "PASS", "stable_weight": stable_weight, "candidate_weight": candidate_weight}
    finally:
        credential.close()


def rollback_and_recover(evidence: Evidence) -> dict[str, Any]:
    before = apim_pool(evidence, candidate_weight=0, stable_weight=100)
    # APIM backend-pool updates propagate asynchronously. Wait for the update
    # to settle before issuing the one bounded recovery request.
    time.sleep(20)
    client = bounded_client(evidence, os.environ["APIM_ENDPOINT"])
    try:
        conversation = client.conversation()
        response = client.turn("Call read_runtime_state and return its JSON.", conversation=conversation)
        snapshot = release_snapshot(response)
        result = {
            "status": "PASS" if snapshot["role"] == "stable" else "FAIL",
            "rollback": before,
            "new_session": {"conversation_id": conversation, **snapshot},
            "new_sessions_route_stable": snapshot["role"] == "stable",
        }
        evidence.write("ROLLBACK_RECOVERY", **result)
        return result
    finally:
        client.close()


def main() -> int:
    evidence = Evidence("phase4_clean_start_e2e")
    started = time.time()
    try:
        canary = apim_pool(evidence, candidate_weight=5, stable_weight=95)
        time.sleep(20)
        local = run_phase4(repetitions=1, write_report=False)
        hosted = hosted_operations(evidence)
        affinity = hosted_affinity_and_fresh(evidence)
        sse = hosted_sse(evidence)
        regression = candidate_regression(evidence)
        rollback = rollback_and_recover(evidence)
        result = {
            "status": "PASS" if all(item.get("status") == "PASS" for item in [canary, hosted, affinity, regression, rollback])
            and local["repeatability"]["Demo A — OFF / ON"]["status"] == "PASS"
            and local["repeatability"]["Demo B — Unknown Correct Path"]["status"] == "PASS"
            and local["repeatability"]["Demo C — Outcome Failure"]["status"] == "PASS"
            and local["repeatability"]["Demo D — Candidate Regression"]["status"] == "PASS"
            else "PARTIAL",
            "clean_start_sequence": [
                "fresh Terraform/azd environment",
                "preflight and infrastructure health",
                "Judge Mode data path via runtime_state",
                "OFF/ON local signature demo",
                "Outcome Failure local signature demo",
                "Candidate Regression hosted Stable/Candidate",
                "APIM rollback to Stable=100/Candidate=0",
                "post-rollback Stable recovery",
            ],
            "local_signature_demos": local["repeatability"],
            "hosted_operations": hosted,
            "apim_weighted_canary": canary,
            "apim_affinity": affinity,
            "apim_sse": sse,
            "hosted_candidate_regression": regression,
            "rollback": rollback,
            "elapsed_seconds": time.time() - started,
            "environment": os.environ.get("AZURE_ENV_NAME"),
        }
        evidence.write("RESULT", **result)
        print(json.dumps({"evidence": str(evidence.path), **result}, indent=2, default=str))
        return 0 if result["status"] == "PASS" else 2
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error))
        print(f"FAIL phase4_clean_start_e2e: {error}\nEvidence: {evidence.path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
