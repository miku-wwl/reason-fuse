# ReasonFuse Phase 1 runtime validation

Implements only the four spikes in
[construction-prompt.md](construction-prompt.md).
Australia East is the only configured region. Independent acceptance is complete:
all four spikes, both full batches, deployed-source identity and clean-start passed.
Read the [final report](verification-report.md) and
[validation boundaries](verification-open-questions.md). The following commands
are reusable procedures, not a request to rerun Phase 1 before learning Phase 2.

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

Reset deletes only hosted test sessions whose IDs were recorded during the
current validation run, resets the external counters, and does not delete
Azure infrastructure. The run's evidence directory is temporary and may be
removed after the conclusions are recorded. Subsequent tests create new native
sessions and approval state.
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

## Independent verification workflow

The corrected fixed batch executes preflight, live environment/package readback,
history (including canonical items and duplicate-input audit), two allow and two
block cases, approve/deny/binding including same-action replay, affinity, exactly
60 new clients, SSE ordering, and telemetry matched to that SSE operation ID:

```powershell
.venv/Scripts/python.exe scripts/verification_batch.py corrected-initial
```

It runs commands sequentially and stops at the first failure; preserve that batch
before diagnosis. Do not rerun a routing sample until it happens to look favorable.
Fresh-cookie clients may share the Azure identity token cache, but never a cookie
jar or HTTP connection. The fixed cohort and all assignments remain recorded.

Only after that batch passes, run the full clean-start workflow. The previously
preserved interpreter was a one-off temporary backup and has been removed. Before
a future run, establish a working pinned recorder environment outside `.venv`;
do not launch the outer recorder from the `.venv` that the workflow replaces, and
do not remove or reuse Terraform ownership state.
The workflow checks the initial batch, resets recorded sessions/counters, preserves
the old .venv under .tools, creates a new one, checks bootstrap tooling, performs
the full deploy (not DnsOnly), reruns the complete fixed suite, and resets again.
It does not tear down infrastructure. Deleted test runtime state is not restored;
the current run may use a temporary evidence directory, which can be removed
after the report has recorded the commands and results.

Deployment generates `src/reasonfuse/validation/build_identity.json`, audits the
native ZIP membership/hashes, deploys roles serially and checks `active` status.
`capture_environment.py` requires both Hosted content_hash values to equal the
audited ZIP SHA-256; preflight also reads the embedded identity from both releases.
Regenerate the identity through deployment after code/lock/Git revision changes.
Never edit it to make a stale upload look current. Use the ordinary native deploy
path in `deploy.ps1` with the pinned tools; do not substitute `--from-package`.

The hosting SDK's `_foundry_responses_history` has load_messages=True for its
within-run tool loop. It is cleared across hosted turns. Synthetic history
validation observes this state and model-bound metadata without changing options
or keeping another canonical transcript. Actual transcript/tool evidence is
available during the validation run; broad message/body telemetry remains
disabled.

`verification_index.py --final` fails unless both full batches and final cleanup
passed. The command creates a final temporary acceptance index for the current
run; it is not an archive requirement and may be removed after the report is
recorded.
`review_verification.py` remains an optional reusable artifact checker; no historical
review is required. Neither indexing nor artifact checking executes live tests.
