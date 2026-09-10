"""Bounded Phase 4 hosted verification.

This script intentionally uses one small APIM/Operations scenario and one
extractive Foundry IQ retrieval.  Evidence is written outside the repository
when REASONFUSE_EVIDENCE_ROOT is set.  It never writes credentials or tokens.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx
from azure.identity import AzureCliCredential

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.support.validation import Evidence, HostedClient, Operations, runtime_state


SEARCH_ENDPOINT = os.environ["SEARCH_ENDPOINT"].rstrip("/")
SEARCH_INDEX = os.environ.get("SEARCH_INDEX", "reasonfuse-phase4-index")
KNOWLEDGE_SOURCE = os.environ.get("KNOWLEDGE_SOURCE", "reasonfuse-phase4-ks")
KNOWLEDGE_BASE = os.environ.get("KNOWLEDGE_BASE", "reasonfuse-phase4-kb")
PROJECT_NAME = os.environ.get(
    "FOUNDRY_PROJECT_NAME",
    os.environ.get("AZURE_AI_PROJECT_NAME", "reasonfuse-phase4"),
)
ACCOUNT_NAME = os.environ.get("FOUNDRY_ACCOUNT_NAME", "cog-e562d26abaf24")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")


def run_apim_operations(evidence: Evidence) -> dict[str, object]:
    """Exercise one allowed diagnostic tool through the real APIM endpoint."""

    external = Operations(evidence)
    external.reset()
    client = HostedClient(evidence, base_url=os.environ["APIM_ENDPOINT"])
    # Keep this bounded probe independent from the generic 600-second
    # integration-client timeout used by the full suite.
    client.http.close()
    client.http = httpx.Client(timeout=httpx.Timeout(150, connect=20))
    try:
        conversation = client.conversation()
        hostname = "api.reasonfuse.local"
        response = client.turn(
            f"Call the dns_resolution tool exactly once for hostname {hostname}.",
            conversation=conversation,
        )
        assert not any(item.get("type") == "mcp_approval_request" for item in response.get("output", []))
        external.assert_counts({f"dns_resolution:{hostname}": 1})
        state = runtime_state(client.turn("Call read_runtime_state and return its JSON.", conversation=conversation))
        audit = [event for event in state.get("middleware_events", []) if "dns_resolution" in event["tool_name"]]
        assert [event["event"] for event in audit] == ["BEFORE", "AFTER"], audit
        evidence.write(
            "APIM_OPERATIONS_ASSERTIONS",
            conversation_id=conversation,
            release=response.get("x_reasonfuse_release") or response.get("release_role"),
            middleware_events=audit,
            external_counts=external.snapshot()["counts"],
        )
        return {"status": "PASS", "conversation_id": conversation, "state": state}
    finally:
        client.close()


def native_iq(evidence: Evidence) -> dict[str, object]:
    """Create/read the bounded IQ objects and perform native retrieval."""

    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        KnowledgeBase,
        KnowledgeSourceReference,
        SearchIndexFieldReference,
        SearchIndexKnowledgeSource,
        SearchIndexKnowledgeSourceParameters,
        SearchFieldDataType,
        SearchIndex,
        SearchableField,
        SimpleField,
    )
    from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
    from azure.search.documents.knowledgebases.models import (
        KnowledgeBaseRetrievalRequest,
        KnowledgeRetrievalMinimalReasoningEffort,
        KnowledgeRetrievalSemanticIntent,
        SearchIndexKnowledgeSourceParams,
    )

    credential = AzureCliCredential(process_timeout=60)
    index_client = SearchIndexClient(SEARCH_ENDPOINT, credential)
    try:
        # A live knowledge source may reference semantic configuration on the
        # index. Do not replace that configuration during a repeatable probe.
        index_client.get_index(SEARCH_INDEX)
    except Exception:
        index = SearchIndex(
            name=SEARCH_INDEX,
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(name="source_url", type=SearchFieldDataType.String, filterable=True),
            ],
        )
        index_client.create_or_update_index(index)
    search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX, credential)
    search_client.upload_documents(
        [
            {
                "id": "rf-phase4-iq-001",
                "title": "ReasonFuse containment policy",
                "content": (
                    "ReasonFuse blocks a repeated no-progress tool loop when the same observed state "
                    "produces no new evidence. The canonical containment action is BLOCK and the "
                    "useful recheck is service_status."
                ),
                "source_url": "https://reasonfuse.local/phase4/containment-policy",
            }
        ]
    )
    source = SearchIndexKnowledgeSource(
        name=KNOWLEDGE_SOURCE,
        description="Version-pinned native Foundry IQ source for Phase 4 validation",
        results_processing="none",
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=SEARCH_INDEX,
            source_data_fields=[
                SearchIndexFieldReference(name="title"),
                SearchIndexFieldReference(name="content"),
                SearchIndexFieldReference(name="source_url"),
            ],
            search_fields=[
                SearchIndexFieldReference(name="title"),
                SearchIndexFieldReference(name="content"),
            ],
        ),
    )
    index_client.create_or_update_knowledge_source(source)
    knowledge_base = KnowledgeBase(
        name=KNOWLEDGE_BASE,
        knowledge_sources=[KnowledgeSourceReference(name=KNOWLEDGE_SOURCE)],
        description="Minimal-cost native IQ retrieval proof",
        output_mode="extractiveData",
        retrieval_reasoning_effort=KnowledgeRetrievalMinimalReasoningEffort(),
    )
    index_client.create_or_update_knowledge_base(knowledge_base)
    retrieval_client = KnowledgeBaseRetrievalClient(
        SEARCH_ENDPOINT,
        credential,
        knowledge_base_name=KNOWLEDGE_BASE,
    )
    request = KnowledgeBaseRetrievalRequest(
        intents=[KnowledgeRetrievalSemanticIntent(search="What does ReasonFuse do when the observed state produces no new evidence?")],
        retrieval_reasoning_effort=KnowledgeRetrievalMinimalReasoningEffort(),
        include_activity=True,
        output_mode="extractiveData",
        knowledge_source_params=[
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name=KNOWLEDGE_SOURCE,
                include_references=True,
                include_reference_source_data=True,
                always_query_source=True,
            )
        ],
        max_output_documents=3,
    )
    result = retrieval_client.retrieve(request).as_dict()
    references = result.get("references", [])
    activities = result.get("activity", [])
    assert references, "Native IQ retrieval returned no references"
    assert any(item.get("type") == "searchIndex" for item in references)
    assert any(item.get("type") == "searchIndex" for item in activities)
    source_data = references[0].get("sourceData") or {}
    assert source_data.get("id") == "rf-phase4-iq-001"
    assert "BLOCK" in json.dumps(result)
    evidence.write(
        "NATIVE_IQ_ASSERTIONS",
        status="PASS",
        search_endpoint=SEARCH_ENDPOINT,
        search_index=SEARCH_INDEX,
        knowledge_source=KNOWLEDGE_SOURCE,
        knowledge_base=KNOWLEDGE_BASE,
        output_mode="extractiveData",
        reference_count=len(references),
        activity_types=[item.get("type") for item in activities],
        citation_url=references[0].get("citationUrl"),
        source_data={key: source_data.get(key) for key in ("id", "title", "source_url")},
    )
    return {
        "status": "PASS",
        "knowledge_source": KNOWLEDGE_SOURCE,
        "knowledge_base": KNOWLEDGE_BASE,
        "reference_count": len(references),
        "activity_types": [item.get("type") for item in activities],
        "citation_url": references[0].get("citationUrl"),
    }


def create_project_connection(evidence: Evidence) -> dict[str, object]:
    """Register the Search KB MCP endpoint in the Foundry project."""

    subscription = os.environ["AZURE_SUBSCRIPTION_ID"]
    resource_group = os.environ["AZURE_RESOURCE_GROUP"]
    project_id = (
        f"/subscriptions/{subscription}/resourceGroups/{resource_group}/"
        f"providers/Microsoft.CognitiveServices/accounts/{ACCOUNT_NAME}/projects/{PROJECT_NAME}"
    )
    name = os.environ.get("FOUNDRY_IQ_CONNECTION", "reasonfuse-phase4-iq")
    target = (
        # The Search Knowledge Base MCP surface currently uses the preview
        # contract below.  The project-connection ARM resource itself uses
        # the stable Foundry project-connections API version.
        f"{SEARCH_ENDPOINT}/knowledgebases/{KNOWLEDGE_BASE}/mcp?api-version=2026-05-01-preview"
    )
    url = f"https://management.azure.com{project_id}/connections/{name}?api-version=2025-06-01"
    body = {
        "name": name,
        "type": "Microsoft.MachineLearningServices/workspaces/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": target,
            "isSharedToAll": True,
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure"},
        },
    }
    token = AzureCliCredential(process_timeout=60).get_token("https://management.azure.com/.default").token
    response = httpx.put(
        url,
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )
    evidence.write("FOUNDRY_IQ_CONNECTION", status_code=response.status_code, connection_name=name, target=target)
    response.raise_for_status()
    return {"status": "PASS", "connection_name": name, "target": target}


def query_cloud_trace(evidence: Evidence, apim_evidence_path: Path) -> dict[str, object]:
    """Look for the known APIM request in the new Log Analytics workspace."""

    az = shutil.which("az.cmd") or shutil.which("az") or "az"
    workspaces = json.loads(
        subprocess.run(
            [az, "monitor", "log-analytics", "workspace", "list", "--resource-group", os.environ["AZURE_RESOURCE_GROUP"], "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    assert len(workspaces) == 1, f"Expected one temporary workspace, found {len(workspaces)}"
    workspace_id = workspaces[0]["customerId"]
    events = [json.loads(line) for line in apim_evidence_path.read_text(encoding="utf-8").splitlines()]
    response_events = [event for event in events if event.get("event") == "RESPONSE"]
    operation_id = next(
        (event.get("headers", {}).get("x-request-id", "").split(",")[0] for event in response_events
         if event.get("headers", {}).get("x-request-id")),
        None,
    )
    assert operation_id, "APIM response did not expose a request identity"
    query = f"""
union isfuzzy=true
(AppRequests | where TimeGenerated > ago(2h) | where OperationId == '{operation_id}' | project TimeGenerated, OperationId, ResultCode, Success, Url, Name),
(AzureDiagnostics | where TimeGenerated > ago(2h) | where correlationId_g == '{operation_id}' or correlationId_s == '{operation_id}' | project TimeGenerated, correlationId_g, correlationId_s, httpStatusCode_d, operationName_s, Resource)
| order by TimeGenerated desc
| take 20
""".strip()
    token = AzureCliCredential(process_timeout=60).get_token("https://api.loganalytics.io/.default").token
    rows: list[list[object]] = []
    last_status = None
    for attempt in range(3):
        response = httpx.post(
            f"https://api.loganalytics.azure.com/v1/workspaces/{workspace_id}/query",
            json={"query": query},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )
        last_status = response.status_code
        response.raise_for_status()
        tables = response.json().get("tables", [])
        rows = tables[0].get("rows", []) if tables else []
        evidence.write("TRACE_QUERY", attempt=attempt + 1, status_code=last_status, operation_id=operation_id, row_count=len(rows))
        if rows:
            break
        if attempt < 2:
            time.sleep(20)
    if not rows:
        return {"status": "NOT VERIFIED", "reason": "No matching AppRequests/AzureDiagnostics row after bounded ingestion wait", "operation_id": operation_id, "query_status": last_status}
    return {"status": "PASS", "operation_id": operation_id, "row_count": len(rows), "query_status": last_status}


def main() -> int:
    evidence = Evidence("phase4_cloud_verify")
    started = time.time()
    try:
        iq = native_iq(evidence)
        connection = create_project_connection(evidence)
        apim = run_apim_operations(evidence)
        apim_path = evidence.path
        trace = query_cloud_trace(evidence, apim_path)
        result = {"native_foundry_iq": iq, "foundry_project_connection": connection, "apim_operations": apim, "cloud_trace": trace}
        evidence.write("RESULT", status="PASS" if trace["status"] == "PASS" else "PARTIAL", results=result, elapsed_seconds=time.time() - started)
        print(json.dumps({"evidence": str(evidence.path), "results": result}, indent=2, default=str))
        return 0 if trace["status"] == "PASS" else 2
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error))
        print(f"FAIL phase4_cloud_verify: {error}\nEvidence: {evidence.path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
