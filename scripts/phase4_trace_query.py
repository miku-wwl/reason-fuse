"""Query the temporary Phase 4 Log Analytics workspace without secrets."""

from __future__ import annotations

import json
import os
import shutil
import subprocess

import httpx
from azure.identity import AzureCliCredential


def main() -> int:
    az = shutil.which("az.cmd") or shutil.which("az") or "az"
    workspaces = json.loads(
        subprocess.run(
            [az, "monitor", "log-analytics", "workspace", "list", "--resource-group", os.environ["AZURE_RESOURCE_GROUP"], "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    workspace_id = workspaces[0]["customerId"]
    query = """
union isfuzzy=true
(AppTraces
 | where TimeGenerated > ago(2h)
 | where Message has_any ('REASONFUSE', 'TURN_START', 'TURN_END', 'RUNTIME_STATE', 'BEFORE', 'AFTER')
 | project Table='AppTraces', TimeGenerated, Message, Properties, OperationId='', Name='', Url=''),
(AppRequests
 | where TimeGenerated > ago(2h)
 | where Url has '/reasonfuse/'
 | project Table='AppRequests', TimeGenerated, Message='', Properties, OperationId, Name, Url)
| order by TimeGenerated desc
| take 100
""".strip()
    token = AzureCliCredential(process_timeout=60).get_token("https://api.loganalytics.io/.default").token
    response = httpx.post(
        f"https://api.loganalytics.azure.com/v1/workspaces/{workspace_id}/query",
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()
    tables = []
    total = 0
    app_traces = 0
    app_requests = 0
    for table in result.get("tables", []):
        rows = table.get("rows", [])
        total += len(rows)
        for row in rows:
            if row and row[0] == "AppTraces":
                app_traces += 1
            elif row and row[0] == "AppRequests":
                app_requests += 1
        tables.append({
            "name": table.get("name"),
            "columns": [column.get("name") for column in table.get("columns", [])],
            "row_count": len(rows),
            "rows": rows[:20],
        })
    print(json.dumps({
        "status_code": response.status_code,
        "matched_rows": total,
        "app_traces_rows": app_traces,
        "app_requests_rows": app_requests,
        "tables": tables,
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
