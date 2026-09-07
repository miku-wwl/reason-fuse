"""Read APIM metadata already ingested into the Phase 1 Log Analytics workspace."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import httpx
from azure.identity import AzureCliCredential

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.support.validation import run_case


def capture(evidence):
    command = [shutil.which("az") or "az", "monitor", "log-analytics", "workspace", "list",
               "--resource-group", os.environ["AZURE_RESOURCE_GROUP"], "--output", "json"]
    workspaces = json.loads(subprocess.run(command, capture_output=True, text=True, check=True).stdout)
    assert len(workspaces) == 1
    workspace_id = workspaces[0]["customerId"]
    query = """AppRequests
| where TimeGenerated > ago(2h)
| where Url startswith 'https://apim-rf-cce5b59dd73ad.azure-api.net/reasonfuse/'
| project TimeGenerated, Name, ResultCode, Success, DurationMs, OperationId, Id, AppRoleName
| order by TimeGenerated desc
| take 20"""
    evidence.write("QUERY", workspace_id=workspace_id, query=query)
    with AzureCliCredential(process_timeout=60) as credential:
        token = credential.get_token("https://api.loganalytics.io/.default").token
        response = httpx.post(f"https://api.loganalytics.azure.com/v1/workspaces/{workspace_id}/query",
                              json={"query": query}, headers={"Authorization": "Bearer " + token}, timeout=120)
    evidence.write("METADATA_QUERY_RESPONSE", status_code=response.status_code, body=response.json())
    response.raise_for_status()
    rows = response.json()["tables"][0]["rows"]
    assert rows, "No APIM request metadata has been ingested in the last two hours"
    assert any(row[2] == "200" and row[3] is True and row[5] for row in rows)
    evidence.write("ASSERTIONS", apim_metadata_rows=len(rows), successful_request_with_operation_id=True)


if __name__ == "__main__":
    run_case("metadata_telemetry", capture)
