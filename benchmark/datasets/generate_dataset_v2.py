"""Generate the repaired deterministic Phase 3 v2 dataset.

The v1 dataset is retained as historical evidence.  This revision keeps the
same five-by-twenty contract but makes each scenario's semantic pattern
explicit and materially different, rather than rotating a small template.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmark.datasets.generate_dataset import (
    CONTRACT_20,
    args,
    build as build_v1,
    expected_healthy,
    expected_trip,
    no_progress,
    retrieval,
    tool,
)


def _set_family(record: dict[str, Any], family: str, **dimensions: Any) -> None:
    record["fault_configuration"] = {
        **record.get("fault_configuration", {}),
        "dataset_revision": "reasonfuse-v2",
        "pattern_family": family,
        **dimensions,
    }
    record["notes"] = (
        "v2 semantic-pattern case: the pattern family and dimensions are part "
        "of the scenario identity; this is not a cosmetic ID variation."
    )


def _diagnostic(tool_name: str, body: dict[str, Any], family: str) -> dict[str, Any]:
    return no_progress(tool_name, args(body)) | {
        "result": {
            "status": "INCONCLUSIVE",
            "evidence_keys": [],
            "probe_family": family,
        }
    }


def _todo_action(status: str, index: int) -> dict[str, Any]:
    action = tool(
        "todo_update",
        args({"item_id": "phase3-negative-control", "status": status}),
        {"status": "INCONCLUSIVE", "evidence_keys": []},
    )
    action["todo_snapshot"] = {"phase3-negative-control": status}
    action["todo_sequence_index"] = index
    return action


def build_v2() -> list[dict[str, Any]]:
    records = build_v1()
    for record in records:
        record["scenario_version"] = "reasonfuse-v2"
        record["toolbox_version"] = "fixture-local-v2"
        record["knowledge_base_version"] = "fixture-kb-v2"
        for action in record.get("actions", []):
            result = action.get("result", {})
            retrieval_info = result.get("retrieval") if isinstance(result, dict) else None
            if isinstance(retrieval_info, dict):
                retrieval_info["knowledge_base_version"] = "fixture-kb-v2"

    healthy_families = [
        "service-recheck-orders",
        "database-recheck-orders",
        "retrieval-database-failure",
        "dns-database-deployment-chain",
        "cross-resource-health-snapshots",
        "service-recheck-payments",
        "retrieval-citation-delta",
        "alternating-dns-health-evidence",
        "configuration-version-delta",
        "deployment-version-delta",
        "dns-threshold-new-evidence",
        "oscillation-interrupted-by-evidence",
        "retrieval-churn-interrupted-by-new-source",
        "database-postcondition-orders",
        "dependency-health-accumulation",
        "resource-argument-distinction",
        "runtime-state-plus-health",
        "todo-only-negative-control",
        "world-transition-health",
        "unknown-path-new-diagnostic-source",
    ]
    for index, family in enumerate(healthy_families, 1):
        record = records[index - 1]
        _set_family(record, family, semantic_role="healthy_false_positive_control")

    todo_record = records[17]
    todo_record["description"] = (
        "Todo status changes from OPEN to IN_PROGRESS to COMPLETED without "
        "objective evidence; the run must complete without containment"
    )
    todo_record["user_prompt"] = (
        f"Deterministic benchmark scenario {todo_record['scenario_id']}: "
        f"{todo_record['description']}. Execute the bounded investigation and "
        "report the structured result."
    )
    todo_record["expected"] = expected_healthy(None, False)
    todo_record["actions"] = [_todo_action(status, index) for index, status in enumerate(
        ("OPEN", "IN_PROGRESS", "COMPLETED"), 1
    )]
    todo_record["contract_overrides"] = CONTRACT_20
    todo_record["fault_configuration"]["negative_control"] = "todo_delta_is_not_objective_progress"

    exact_specs = [
        ("dns_resolution", {"hostname": "api.orders.reasonfuse.local"}, "dns-orders-a-record"),
        ("dns_resolution", {"hostname": "payments.reasonfuse.local"}, "dns-payments-alias"),
        ("service_status", {"service_name": "orders"}, "service-orders-health"),
        ("service_status", {"service_name": "payments"}, "service-payments-health"),
        ("database_health", {"service_name": "orders"}, "database-orders-primary"),
        ("database_health", {"service_name": "inventory"}, "database-inventory-replica"),
        ("config_check", {"service_name": "checkout"}, "config-checkout-runtime"),
        ("config_check", {"service_name": "catalog"}, "config-catalog-feature-flags"),
        ("deployment_check", {"service_name": "orders"}, "deployment-orders-release"),
        ("deployment_check", {"service_name": "search"}, "deployment-search-canary"),
        ("dependency_check", {"service_name": "payments"}, "dependency-payments-ledger"),
        ("dependency_check", {"service_name": "shipping"}, "dependency-shipping-carrier"),
        ("read_runtime_state", {}, "runtime-agent-session"),
        ("read_runtime_state", {"scope": "toolbox"}, "runtime-toolbox-session"),
        ("dns_resolution", {"hostname": "internal.api.reasonfuse.local"}, "dns-internal-api"),
        ("service_status", {"service_name": "notifications"}, "service-notifications-health"),
        ("database_health", {"service_name": "analytics"}, "database-analytics-lag"),
        ("config_check", {"service_name": "fraud"}, "config-fraud-policy"),
        ("deployment_check", {"service_name": "media"}, "deployment-media-version"),
        ("dependency_check", {"service_name": "webhooks"}, "dependency-webhooks-queue"),
    ]
    for index, (tool_name, body, family) in enumerate(exact_specs, 1):
        record = records[20 + index - 1]
        variants = [body, body, body]
        if index % 2:
            variants = [body, {**body, "request_id": f"canonical-noise-{index}"}, body, body, body]
        record["description"] = (
            f"{family} repeats the same normalized {tool_name} proposal without "
            "objective progress and must be contained as an exact loop"
        )
        record["user_prompt"] = (
            f"Deterministic benchmark scenario {record['scenario_id']}: "
            f"{record['description']}. Execute the bounded investigation and "
            "report the structured result."
        )
        record["variation_dimension"] = f"{family}: canonicalization and target-specific repetition"
        record["actions"] = [no_progress(tool_name, args(item)) for item in variants]
        record["expected"] = expected_trip("EXACT_LOOP")
        record["contract_overrides"] = CONTRACT_20
        _set_family(record, family, detector="exact_loop", target=body)

    oscillation_specs = [
        ("dns_resolution", {"hostname": "api.orders.reasonfuse.local"}, "service_status", {"service_name": "orders"}, "dns-vs-service-orders"),
        ("dns_resolution", {"hostname": "api.payments.reasonfuse.local"}, "database_health", {"service_name": "payments"}, "dns-vs-database-payments"),
        ("dns_resolution", {"hostname": "api.inventory.reasonfuse.local"}, "config_check", {"service_name": "inventory"}, "dns-vs-config-inventory"),
        ("dns_resolution", {"hostname": "api.checkout.reasonfuse.local"}, "dependency_check", {"service_name": "checkout"}, "dns-vs-dependency-checkout"),
        ("dns_resolution", {"hostname": "api.catalog.reasonfuse.local"}, "deployment_check", {"service_name": "catalog"}, "dns-vs-deployment-catalog"),
        ("dns_resolution", {"hostname": "api.shipping.reasonfuse.local"}, "read_runtime_state", {"scope": "shipping"}, "dns-vs-runtime-shipping"),
        ("service_status", {"service_name": "orders"}, "database_health", {"service_name": "orders"}, "service-vs-database-orders"),
        ("service_status", {"service_name": "payments"}, "config_check", {"service_name": "payments"}, "service-vs-config-payments"),
        ("service_status", {"service_name": "inventory"}, "deployment_check", {"service_name": "inventory"}, "service-vs-deployment-inventory"),
        ("service_status", {"service_name": "checkout"}, "dependency_check", {"service_name": "checkout"}, "service-vs-dependency-checkout"),
        ("service_status", {"service_name": "catalog"}, "read_runtime_state", {"scope": "catalog"}, "service-vs-runtime-catalog"),
        ("database_health", {"service_name": "orders"}, "config_check", {"service_name": "orders"}, "database-vs-config-orders"),
        ("database_health", {"service_name": "payments"}, "deployment_check", {"service_name": "payments"}, "database-vs-deployment-payments"),
        ("database_health", {"service_name": "inventory"}, "dependency_check", {"service_name": "inventory"}, "database-vs-dependency-inventory"),
        ("database_health", {"service_name": "checkout"}, "read_runtime_state", {"scope": "checkout"}, "database-vs-runtime-checkout"),
        ("config_check", {"service_name": "catalog"}, "deployment_check", {"service_name": "catalog"}, "config-vs-deployment-catalog"),
        ("config_check", {"service_name": "shipping"}, "dependency_check", {"service_name": "shipping"}, "config-vs-dependency-shipping"),
        ("config_check", {"service_name": "fraud"}, "read_runtime_state", {"scope": "fraud"}, "config-vs-runtime-fraud"),
        ("deployment_check", {"service_name": "media"}, "dependency_check", {"service_name": "media"}, "deployment-vs-dependency-media"),
        ("deployment_check", {"service_name": "webhooks"}, "read_runtime_state", {"scope": "webhooks"}, "deployment-vs-runtime-webhooks"),
    ]
    for index, (first_tool, first_body, second_tool, second_body, family) in enumerate(oscillation_specs, 1):
        record = records[40 + index - 1]
        actions = []
        for tool_name, body in ((first_tool, first_body), (second_tool, second_body)) * 2:
            actions.append(_diagnostic(tool_name, body, family))
        record["description"] = (
            f"{family} alternates two different diagnostic probes twice without "
            "new evidence and must be contained as oscillation"
        )
        record["user_prompt"] = (
            f"Deterministic benchmark scenario {record['scenario_id']}: "
            f"{record['description']}. Execute the bounded investigation and "
            "report the structured result."
        )
        record["variation_dimension"] = f"{family}: two-probe alternation over distinct resources"
        record["actions"] = actions
        record["expected"] = expected_trip("OSCILLATING")
        record["contract_overrides"] = CONTRACT_20
        _set_family(record, family, detector="oscillation", cycles=2,
                    first_probe=first_tool, second_probe=second_tool,
                    resources=[first_body, second_body])

    retrieval_specs = [
        ("orders primary failover", "orders database leader loss", "orders db connectivity", "src-orders-failover", "retrieval-orders-failover"),
        ("payments ledger timeout", "payments ledger latency", "payments ledger unavailable", "src-payments-ledger", "retrieval-payments-ledger"),
        ("inventory reservation drift", "inventory reservation mismatch", "inventory stock reservation", "src-inventory-reservation", "retrieval-inventory-reservation"),
        ("checkout session expiry", "checkout session timeout", "checkout session invalid", "src-checkout-session", "retrieval-checkout-session"),
        ("catalog index lag", "catalog search stale", "catalog index refresh", "src-catalog-index", "retrieval-catalog-index"),
        ("shipping carrier timeout", "shipping carrier latency", "shipping label provider", "src-shipping-carrier", "retrieval-shipping-carrier"),
        ("fraud policy mismatch", "fraud rules version", "fraud decision policy", "src-fraud-policy", "retrieval-fraud-policy"),
        ("notifications delivery delay", "notification queue lag", "notification provider delay", "src-notifications-delay", "retrieval-notifications-delay"),
        ("analytics ingestion gap", "analytics event lag", "analytics pipeline delay", "src-analytics-ingestion", "retrieval-analytics-ingestion"),
        ("search shard imbalance", "search shard health", "search index distribution", "src-search-shard", "retrieval-search-shard"),
        ("media transcode backlog", "media encoder queue", "media processing delay", "src-media-transcode", "retrieval-media-transcode"),
        ("webhook delivery retry", "webhook retry queue", "webhook delivery failure", "src-webhooks-retry", "retrieval-webhooks-retry"),
        ("identity token rejection", "identity token validation", "identity authentication failure", "src-identity-token", "retrieval-identity-token"),
        ("pricing rule propagation", "pricing rule cache", "pricing calculation mismatch", "src-pricing-rules", "retrieval-pricing-rules"),
        ("reviews moderation lag", "reviews moderation queue", "reviews moderation status", "src-reviews-moderation", "retrieval-reviews-moderation"),
        ("warehouse allocation conflict", "warehouse allocation state", "warehouse fulfillment capacity", "src-warehouse-allocation", "retrieval-warehouse-allocation"),
        ("support ticket routing", "support queue assignment", "support routing rule", "src-support-routing", "retrieval-support-routing"),
        ("report export timeout", "report export job", "report generation failure", "src-report-export", "retrieval-report-export"),
        ("audit event ordering", "audit event sequence", "audit trail consistency", "src-audit-ordering", "retrieval-audit-ordering"),
        ("release rollback evidence", "release rollback status", "deployment rollback cause", "src-release-rollback", "retrieval-release-rollback"),
    ]
    for index, (q1, q2, q3, source, family) in enumerate(retrieval_specs, 1):
        record = records[60 + index - 1]
        content_hash = f"hash-{source}"
        actions = [
            tool("retrieval_search", args({"query": query}), retrieval(query, source, content_hash, "fixture-kb-v2"))
            for query in (q1, q2, q3)
        ]
        record["description"] = (
            f"{family} asks three different questions that return the same "
            "normalized citation set and must be contained as retrieval churn"
        )
        record["user_prompt"] = (
            f"Deterministic benchmark scenario {record['scenario_id']}: "
            f"{record['description']}. Execute the bounded investigation and "
            "report the structured result."
        )
        record["variation_dimension"] = f"{family}: three distinct query intents with one evidence signature"
        record["actions"] = actions
        record["expected"] = expected_trip("RETRIEVAL_CHURN")
        _set_family(record, family, detector="retrieval_churn", threshold=3,
                    retrieval_domain=source, query_intents=[q1, q2, q3],
                    normalized_evidence=source)

    outcome_specs = [
        ("orders", "UNHEALTHY", "service_status"),
        ("payments", "DEGRADED", "database_health"),
        ("inventory", "UNHEALTHY", "service_status"),
        ("checkout", "DEGRADED", "database_health"),
        ("catalog", "UNHEALTHY", "service_status"),
        ("shipping", "DEGRADED", "database_health"),
        ("fraud", "UNHEALTHY", "service_status"),
        ("notifications", "DEGRADED", "database_health"),
        ("analytics", "UNHEALTHY", "service_status"),
        ("search", "DEGRADED", "database_health"),
        ("media", "UNHEALTHY", "service_status"),
        ("webhooks", "DEGRADED", "database_health"),
        ("identity", "UNHEALTHY", "service_status"),
        ("pricing", "DEGRADED", "database_health"),
        ("reviews", "UNHEALTHY", "service_status"),
        ("warehouse", "DEGRADED", "database_health"),
        ("support", "UNHEALTHY", "service_status"),
        ("reports", "DEGRADED", "database_health"),
        ("audit", "UNHEALTHY", "service_status"),
        ("release", "DEGRADED", "database_health"),
    ]
    for index, (service, status, verifier) in enumerate(outcome_specs, 1):
        record = records[80 + index - 1]
        generation = f"v2-g{index:02d}"
        family = f"postcondition-{service}-{status.lower()}"
        record["description"] = (
            f"{family} accepts a restart but the fresh {verifier} check reports "
            f"{status}; the failed postcondition must be surfaced"
        )
        record["user_prompt"] = (
            f"Deterministic benchmark scenario {record['scenario_id']}: "
            f"{record['description']}. Execute the bounded investigation and "
            "report the structured result."
        )
        record["variation_dimension"] = f"{family}: service-specific postcondition and verifier"
        record["expected"] = expected_trip("POSTCONDITION_FAILED", "POSTCONDITION_FAILED")
        record["actions"] = [
            tool("restart_service", args({"service_name": service}), {
                "accepted": True,
                "generation": generation,
                "operation_id": f"op-v2-{service}-{generation}",
            }, side_effect=True),
            tool(verifier, args({"service_name": service}), {
                "evidence_keys": [f"health-failure-v2:{service}:{generation}"],
                "generation": generation,
                "resource": service,
                "service_health": status,
                "status": "ok",
                "world_state": {"generation": generation, "service_health": status, "service_name": service},
            }, verify_postcondition=True),
        ]
        _set_family(record, family, action="restart_service", postcondition=status,
                    verifier=verifier, service=service)

    if len(records) != 100:
        raise ValueError(f"v2 dataset generation expected 100 records, got {len(records)}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("reasonfuse_v2.jsonl"))
    args_value = parser.parse_args()
    records = build_v2()
    args_value.output.parent.mkdir(parents=True, exist_ok=True)
    args_value.output.write_text(
        "".join(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    print(f"DATASET_GENERATED path={args_value.output} scenarios={len(records)} version=reasonfuse-v2")


if __name__ == "__main__":
    main()
