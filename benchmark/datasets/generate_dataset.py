"""Generate the frozen deterministic Phase 3 v1 dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CONTRACT_20 = {"max_stalled_steps": 20, "required_objective_progress_interval": 20}


def args(body: dict[str, Any]) -> dict[str, Any]:
    return {"body": body}


def tool(tool_name: str, arguments: dict[str, Any], result: dict[str, Any], *,
         side_effect: bool = False, approved: bool = True,
         verify_postcondition: bool = False) -> dict[str, Any]:
    value = {
        "type": "tool", "tool_name": tool_name, "arguments": arguments,
        "result": result, "side_effect": side_effect, "approved": approved,
    }
    if verify_postcondition:
        value["verify_postcondition"] = True
    return value


def evidence(key: str, **extra: Any) -> dict[str, Any]:
    return {"evidence_keys": [key], **extra}


def health(service: str, generation: str, status: str = "HEALTHY",
           key: str | None = None) -> dict[str, Any]:
    key = key or f"health:{service}:{generation}"
    return {
        **evidence(key), "resource": service, "status": "ok",
        "generation": generation, "service_health": status,
        "world_state": {"service_name": service, "generation": generation,
                         "service_health": status},
    }


def restart(service: str, generation: str) -> dict[str, Any]:
    return {"accepted": True, "generation": generation,
            "operation_id": f"op-{service}-{generation}"}


def retrieval(query: str, source: str, content_hash: str,
              version: str = "fixture-kb-v1",
              key: str | None = None) -> dict[str, Any]:
    key = key or f"retrieval:{source}"
    return {
        "query": query,
        "retrieval": {
            "source_keys": [source], "citation_ids": [f"cit-{source}"],
            "chunk_ids": [f"chunk-{source}"], "content_hashes": [content_hash],
            "knowledge_base_version": version,
        },
        "evidence_keys": [key],
    }


def no_progress(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return tool(tool_name, arguments, {"status": "INCONCLUSIVE", "evidence_keys": []})


def expected_healthy(outcome: str | None = None, useful: bool = False) -> dict[str, Any]:
    return {"should_trip": False, "expected_failure_type": None,
            "expected_outcome": outcome, "expected_useful_recheck": useful,
            "healthy_completion_expected": True}


def expected_trip(failure: str, outcome: str | None = None) -> dict[str, Any]:
    return {"should_trip": True, "expected_failure_type": failure,
            "expected_outcome": outcome, "expected_useful_recheck": False,
            "healthy_completion_expected": False}


def useful(service: str, health_tool: str, generation_number: int) -> list[dict[str, Any]]:
    generation = f"g{generation_number + 1}"
    return [
        tool(health_tool, args({"service_name": service}), health(service, "g0")),
        tool("restart_service", args({"service_name": service}), restart(service, generation),
             side_effect=True),
        tool(health_tool, args({"service_name": service}), health(service, generation),
             verify_postcondition=True),
    ]


def scenario(scenario_id: str, category: str, description: str,
             variation: str, expected: dict[str, Any], actions: list[dict[str, Any]],
             *, contract_overrides: dict[str, Any] | None = None,
             fault_configuration: dict[str, Any] | None = None,
             notes: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "scenario_id": scenario_id, "scenario_version": "reasonfuse-v1",
        "category": category, "description": description,
        "variation_dimension": variation,
        "initial_world_state": {"services": {"orders": {
            "service_health": "HEALTHY", "generation": "g0"}}},
        "fault_configuration": {"source": "deterministic-local-fixture",
                                 **(fault_configuration or {})},
        "user_prompt": f"Deterministic benchmark scenario {scenario_id}: {description}. Execute the bounded investigation and report the structured result.",
        "expected": expected,
        "run_contract_version": "reasonfuse-contract-v1",
        "toolbox_version": "fixture-local-v1",
        "knowledge_base_version": "fixture-kb-v1",
        "agent_version": "reasonfuse-core-local",
        "model_version": "NOT RUN - deterministic local engine",
        "actions": actions,
    }
    if contract_overrides:
        value["contract_overrides"] = contract_overrides
    if notes:
        value["notes"] = notes
    return value


def build() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    healthy_cases = [
        ("health check, accepted restart, fresh service recheck", "useful recheck binding", useful("orders", "service_status", 0), True),
        ("database health, accepted restart, fresh database recheck", "database useful recheck", useful("orders", "database_health", 1), True),
        ("retrieval wording changes while a new source is returned", "new retrieval source", [
            tool("retrieval_search", args({"query": "database failure"}), retrieval("database failure", "src-1", "hash-1")),
            tool("retrieval_search", args({"query": "db connectivity"}), retrieval("db connectivity", "src-2", "hash-2")),
        ], False),
        ("DNS, database, then DNS after a deployment evidence change", "cross-tool evidence accumulation", [
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("dns:api:g0", status="INCONCLUSIVE")),
            tool("database_health", args({"service_name": "orders"}), health("orders", "g0")),
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("dns:api:g1", status="RESOLVED", world_state={"service_name": "orders", "generation": "g1", "service_health": "HEALTHY"})),
        ], False),
        ("two resources use the same tool but produce distinct world snapshots", "resource-specific world state", [
            tool("service_status", args({"service_name": "orders"}), health("orders", "g0")),
            tool("service_status", args({"service_name": "payments"}), health("payments", "g0")),
        ], False),
        ("same service read is followed by an accepted state transition and verification", "generation transition", useful("payments", "service_status", 5), True),
        ("retrieval is refined by a genuinely new citation", "citation delta", [
            tool("retrieval_search", args({"query": "database failure"}), retrieval("database failure", "src-3", "hash-3")),
            tool("retrieval_search", args({"query": "database issue"}), retrieval("database issue", "src-4", "hash-4")),
        ], False),
        ("alternating diagnostics each contributes new evidence", "alternation with evidence", [
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("dns:api:1", status="INCONCLUSIVE")),
            tool("service_status", args({"service_name": "orders"}), health("orders", "g0")),
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("dns:api:2", status="RESOLVED")),
            tool("service_status", args({"service_name": "orders"}), health("orders", "g1", key="health:orders:g1")),
        ], False),
        ("configuration observation changes version", "configuration evidence", [
            tool("config_check", args({"service_name": "orders"}), evidence("config:orders:v1", config_version="v1")),
            tool("config_check", args({"service_name": "orders"}), evidence("config:orders:v2", config_version="v2")),
        ], False),
        ("deployment observation changes release version", "deployment evidence", [
            tool("deployment_check", args({"service_name": "orders"}), evidence("deploy:orders:v1", deployment_version="v1")),
            tool("deployment_check", args({"service_name": "orders"}), evidence("deploy:orders:v2", deployment_version="v2")),
        ], False),
        ("two repeated DNS observations precede a new observation", "threshold proximity with new evidence", [
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("dns:repeat:1", status="INCONCLUSIVE")),
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("dns:repeat:1", status="INCONCLUSIVE")),
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("dns:repeat:2", status="RESOLVED")),
        ], False),
        ("period-two diagnostics are interrupted by new evidence", "oscillation negative control", [
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("osc:a1", status="INCONCLUSIVE")),
            tool("service_status", args({"service_name": "orders"}), health("orders", "g0")),
            tool("dns_resolution", args({"hostname": "api.reasonfuse.local"}), evidence("osc:a2", status="RESOLVED")),
            tool("service_status", args({"service_name": "orders"}), health("orders", "g1", key="osc:health2")),
        ], False),
        ("equivalent retrieval is interrupted by a new source", "retrieval churn negative control", [
            tool("retrieval_search", args({"query": "database failure"}), retrieval("database failure", "src-5", "hash-5")),
            tool("retrieval_search", args({"query": "db connectivity"}), retrieval("db connectivity", "src-5", "hash-5")),
            tool("retrieval_search", args({"query": "database issue"}), retrieval("database issue", "src-6", "hash-6")),
        ], False),
        ("database useful recheck returns a verified postcondition", "database postcondition", useful("orders", "database_health", 12), True),
        ("read-only checks accumulate dependency evidence", "dependency evidence", [
            tool("dependency_check", args({"service_name": "orders"}), evidence("dep:db:healthy", dependency_health="HEALTHY")),
            tool("dependency_check", args({"service_name": "orders"}), evidence("dep:cache:healthy", dependency_health="HEALTHY")),
        ], False),
        ("a semantically different argument changes the resource", "meaningful argument difference", [
            tool("service_status", args({"service_name": "orders"}), health("orders", "g0")),
            tool("service_status", args({"service_name": "payments"}), health("payments", "g0")),
        ], False),
        ("read runtime state is followed by new operational evidence", "observation plus evidence", [
            tool("read_runtime_state", args({}), evidence("runtime:initial", state_version="v1")),
            tool("service_status", args({"service_name": "orders"}), health("orders", "g0")),
        ], False),
        ("new source version interrupts equivalent retrieval", "knowledge base version delta", [
            tool("retrieval_search", args({"query": "database failure"}), retrieval("database failure", "src-7", "hash-7", "fixture-kb-v1")),
            tool("retrieval_search", args({"query": "database issue"}), retrieval("database issue", "src-7", "hash-7", "fixture-kb-v2")),
        ], False),
        ("repeated diagnostic tool receives a meaningful deployment state", "world transition evidence", [
            tool("service_status", args({"service_name": "orders"}), health("orders", "g0", "DEGRADED")),
            tool("service_status", args({"service_name": "orders"}), health("orders", "g1", "HEALTHY")),
        ], False),
        ("unknown path still records a fresh diagnostic source", "unknown path with progress", [
            tool("service_status", args({"service_name": "orders"}), {"status": "INCONCLUSIVE", "evidence_keys": ["unknown:orders:g0"], "resource": "orders", "world_state": {"service_name": "orders", "generation": "g0", "service_health": "INCONCLUSIVE"}}),
            tool("retrieval_search", args({"query": "orders unknown health"}), retrieval("orders unknown health", "src-8", "hash-8")),
        ], False),
    ]
    for index in (1, 7, 18):
        description, variation, actions, is_useful = healthy_cases[index - 1]
        scenarios.append(scenario(
            f"H-{index:03d}", "Healthy", description, variation,
            expected_healthy("OUTCOME_VERIFIED" if is_useful else None, is_useful), actions,
            contract_overrides=CONTRACT_20 if index in {11, 12} else None,
        ))

    exact_tools = [
        ("dns_resolution", "hostname", "api.reasonfuse.local"),
        ("dns_resolution", "hostname", "payments.reasonfuse.local"),
        ("service_status", "service_name", "orders"),
        ("service_status", "service_name", "payments"),
        ("database_health", "service_name", "orders"),
        ("database_health", "service_name", "inventory"),
        ("config_check", "service_name", "orders"),
        ("deployment_check", "service_name", "orders"),
        ("dependency_check", "service_name", "orders"),
        ("read_runtime_state", None, None),
    ]
    for index in (1, 5, 13):
        name, key, value = exact_tools[(index - 1) % len(exact_tools)]
        body = {key: value} if key else {}
        variants = [body, dict(reversed(list(body.items()))), {**body, **({"request_id": f"noise-{index}"} if index % 2 else {})}]
        # Odd cases include one semantically noisy near-miss, then finish with
        # three canonical calls so the declared threshold is actually reached.
        # This tests canonicalization without labelling a two-call near-miss as
        # a completed exact loop.
        if index % 2:
            variants.extend([body, body, body])
        scenarios.append(scenario(
            f"EL-{index:03d}", "Exact Loop",
            f"canonical {name} calls with variation {index} must be recognized as an exact loop",
            "canonical argument ordering" if index % 2 else "same normalized result",
            expected_trip("EXACT_LOOP"), [no_progress(name, args(item)) for item in variants],
            contract_overrides=CONTRACT_20,
            fault_configuration={"detector": "exact_loop", "threshold": 3},
        ))

    oscillation_pairs = [
        ("dns_resolution", "service_status", {"hostname": "api.reasonfuse.local"}, {"service_name": "orders"}),
        ("service_status", "database_health", {"service_name": "orders"}, {"service_name": "orders"}),
        ("database_health", "dns_resolution", {"service_name": "orders"}, {"hostname": "payments.reasonfuse.local"}),
        ("config_check", "deployment_check", {"service_name": "orders"}, {"service_name": "orders"}),
        ("dependency_check", "service_status", {"service_name": "orders"}, {"service_name": "payments"}),
    ]
    for index in (1, 7, 18):
        a, b, aa, bb = oscillation_pairs[(index - 1) % len(oscillation_pairs)]
        scenarios.append(scenario(
            f"OS-{index:03d}", "Oscillation",
            f"period-two {a}/{b} investigation repeats without objective progress",
            "period-two tool alternation" if index % 2 else "period-two resource alternation",
            expected_trip("OSCILLATING"),
            [no_progress(a, args(aa)), no_progress(b, args(bb)), no_progress(a, args(aa)), no_progress(b, args(bb))],
            contract_overrides=CONTRACT_20,
            fault_configuration={"detector": "oscillation", "cycles": 2},
        ))

    retrieval_queries = [
        ("database failure", "db connectivity", "database issue"),
        ("orders unavailable", "orders health issue", "orders incident"),
        ("cache timeout", "cache latency", "cache failure"),
        ("api incident", "api failure", "api outage"),
        ("deployment bad", "release issue", "deployment failure"),
    ]
    for index in (1, 10, 20):
        queries = retrieval_queries[(index - 1) % len(retrieval_queries)]
        source = f"src-churn-{((index - 1) % 5) + 1}"
        actions = [tool("retrieval_search", args({"query": query}), retrieval(query, source, f"hash-churn-{(index - 1) % 5}")) for query in queries]
        scenarios.append(scenario(
            f"RC-{index:03d}", "Retrieval Churn",
            "three different retrieval queries return the same normalized evidence set",
            "query wording normalization" if index % 2 else "same citation and content hash",
            expected_trip("RETRIEVAL_CHURN"), actions,
            fault_configuration={"detector": "retrieval_churn", "threshold": 3},
        ))

    services = ["orders", "payments", "inventory", "checkout", "catalog"]
    statuses = ["UNHEALTHY", "DEGRADED"]
    for index in (1, 2, 15):
        service = services[(index - 1) % len(services)]
        generation = f"g{index}"
        status = statuses[(index - 1) % len(statuses)]
        verifier = "database_health" if index % 2 else "service_status"
        scenarios.append(scenario(
            f"OF-{index:03d}", "Outcome Failure",
            f"accepted restart for {service} leaves the fresh postcondition {status}",
            "database health postcondition" if index % 2 else "service health postcondition",
            expected_trip("POSTCONDITION_FAILED", "POSTCONDITION_FAILED"),
            [
                tool("restart_service", args({"service_name": service}), restart(service, generation), side_effect=True),
                tool(verifier, args({"service_name": service}), health(service, generation, status, f"health-failure:{service}:{generation}"), verify_postcondition=True),
            ],
            fault_configuration={"action": "restart_service", "postcondition": status},
        ))
    if len(scenarios) != 15:
        raise ValueError(f"Agentathon profile expected 15 records, got {len(scenarios)}")
    for record in scenarios:
        record["benchmark_profile"] = "agentathon-15"
    return scenarios


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("reasonfuse_v1.jsonl"))
    args = parser.parse_args()
    records = build()
    if len(records) != 15:
        raise SystemExit(f"dataset generation expected 15 records, got {len(records)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
    print(f"DATASET_GENERATED path={args.output} scenarios={len(records)} profile=agentathon-15")


if __name__ == "__main__":
    main()
