"""Read APIM metadata already ingested into the Phase 1 Log Analytics workspace."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx
from azure.identity import AzureCliCredential

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.support.validation import run_case, EVIDENCE_ROOT


def capture(evidence):
    command = [shutil.which("az") or "az", "monitor", "log-analytics", "workspace", "list",
               "--resource-group", os.environ["AZURE_RESOURCE_GROUP"], "--output", "json"]
    workspaces = json.loads(subprocess.run(command, capture_output=True, text=True, check=True).stdout)
    assert len(workspaces) == 1
    workspace_id = workspaces[0]["customerId"]
    sse_path = max((EVIDENCE_ROOT / "runs").rglob("*-spike04_sse.jsonl"), key=lambda p: p.name)
    events = [json.loads(line) for line in sse_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1].get("status") == "PASS", "Latest SSE probe did not pass"
    stream = next(event for event in events if event["event"] == "STREAM_HEADERS")
    operation_id = stream["headers"]["x-request-id"].split(",")[0]
    assert len(operation_id) == 32 and all(c in "0123456789abcdef" for c in operation_id)
    query = """AppRequests
| where TimeGenerated > ago(2h)
| where Url startswith 'https://apim-rf-cce5b59dd73ad.azure-api.net/reasonfuse/'
| where OperationId == 'OPERATION_ID'
| project TimeGenerated, Name, ResultCode, Success, DurationMs, OperationId, Id, AppRoleName
| order by TimeGenerated desc
| take 20""".replace("OPERATION_ID", operation_id)
    evidence.write("QUERY", workspace_id=workspace_id, query=query, matched_sse_evidence=str(sse_path),
                   stream_response_timestamp_utc=stream["timestamp_utc"], operation_id=operation_id)
    with AzureCliCredential(process_timeout=60) as credential:
        token = credential.get_token("https://api.loganalytics.io/.default").token
        for attempt in range(5):
            response = httpx.post(f"https://api.loganalytics.azure.com/v1/workspaces/{workspace_id}/query",
                                  json={"query": query}, headers={"Authorization": "Bearer " + token}, timeout=120)
            evidence.write("METADATA_QUERY_RESPONSE", attempt=attempt + 1, status_code=response.status_code, body=response.json())
            response.raise_for_status()
            rows = response.json()["tables"][0]["rows"]
            if rows:
                break
            if attempt < 4:
                evidence.write("INGESTION_WAIT", seconds=30)
                print("Current SSE metadata not ingested yet; checking again in 30 seconds.", flush=True)
                time.sleep(30)
    assert rows, "No APIM request metadata has been ingested in the last two hours"
    assert any(row[2] == "200" and row[3] is True and row[5] for row in rows)
    assert all(row[5] == operation_id for row in rows)
    evidence.write("ASSERTIONS", apim_metadata_rows=len(rows), successful_request_with_operation_id=True,
                   current_sse_operation_id=operation_id)


if __name__ == "__main__":
    run_case("metadata_telemetry", capture)
