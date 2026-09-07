# ReasonFuse Phase 1 runtime validation

Implements only the four spikes in
[construction-prompt.md](construction-prompt.md).
Australia East is the only configured region. Construction is complete: all nine
real integration cases, full preflight and reset passed. Read
[report.md](report.md) for evidence and limits. The separate
independent Phase 1 validation remains pending.

## Run from the repository root on Windows

```powershell
pwsh -File scripts/bootstrap.ps1
pwsh -File scripts/deploy.ps1
pwsh -File scripts/preflight.ps1
.venv/Scripts/python.exe tests/integration/history_session.py
.venv/Scripts/python.exe tests/integration/toolbox_interception.py allow
.venv/Scripts/python.exe tests/integration/toolbox_interception.py block
.venv/Scripts/python.exe tests/integration/approval.py approve
.venv/Scripts/python.exe tests/integration/approval.py deny
.venv/Scripts/python.exe tests/integration/approval.py binding
.venv/Scripts/python.exe tests/integration/apim.py affinity
.venv/Scripts/python.exe tests/integration/apim.py new_session_control --samples 60
.venv/Scripts/python.exe tests/integration/apim.py sse
.venv/Scripts/python.exe scripts/capture_telemetry.py
pwsh -File scripts/reset.ps1
```

Run validation cases sequentially: the deterministic external counters are shared.
Stop and preserve evidence on a failed frozen assumption. Do not add another
history store, session manager, transport or approval database to make a test pass.
The scripts do not automatically mark the report PASS.

The `.sh` entry points invoke the PowerShell implementations through `pwsh`.
These wrappers target Windows/Git Bash with PowerShell 7, not an untested Linux
deployment environment. `deploy.ps1 -DnsOnly` provisions the initial DNS-only
Toolbox; omit the flag to add the R2 restart tool.

The Operations API is a deterministic test service. `restart_service` records a
simulated restart and never operates on a real service. Counters are independent
of the agent, and an epoch change causes validation to fail rather than accepting
a reset counter as proof that no call occurred. Only the counter/reset endpoints
use the generated administration key, which stays in the ignored azd environment.

Reset deletes only hosted test sessions whose IDs are recorded in these evidence
files under `evidence/phase-01-runtime-validation/`, resets the external counters, and retains evidence. It does not delete Azure
infrastructure. Subsequent tests create new native sessions and approval state.
Reset verifies that recorded hosted sessions are absent or explicitly `deleted`,
and external counters are still zero. Foundry can retain deleted metadata rows.
Run reset after the validation commands have finished.

APIM forwards the caller's Entra bearer token to Foundry, where caller RBAC is
enforced. No APIM subscription key or custom user impersonation is used. Keep one
HTTP client/cookie jar per logical client session. New-cookie controls measure
escape from affinity, not a statistically precise 95/5 ratio.

The RF_RELEASE_PROBE and RF_SSE_PROBE inputs exercise deterministic Agent Framework
middleware through the real Hosted Agent endpoint. They intentionally avoid model
inference for repeatable routing and chunk timing; the other spikes use the real
Foundry model and the actual tool-calling loop.

`capture_telemetry.py` reads recently ingested APIM request metadata from Log
Analytics. Ingestion can lag; it exits non-zero if no recent APIM records are found.

Dependency locks are authoritative; code deployment uploads exact `requirements.txt`
for remote build. `.agentignore` excludes environment files, local tools, evidence
and infrastructure state from the upload. No Full Harness bundle is used.
