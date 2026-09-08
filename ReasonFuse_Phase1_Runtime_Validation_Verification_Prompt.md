# ReasonFuse Phase 1 — Runtime Validation Verification Prompt

> **Purpose:** Independently validate the Phase 1 runtime construction against the frozen ReasonFuse v4.1.3 architecture.  
> **Audience:** GPT-6 Astra / independent validation agent  
> **Phase:** 1 — Runtime Validation  
> **Role:** Validator, not implementer  
> **Rule:** Do not award PASS based on code inspection alone.  
> **Status:** Phase 1 acceptance completed on 2026-09-08. This document retains the reusable rubric; it is not a new execution or historical-review task.

---

# 0. Current Repository and Acceptance Baseline

ReasonFuse is one project. Phase 1 is a validation scope within that project.
Run commands from the repository root, currently `D:\workshop\sep\reason-fuse`.
Do not recreate a separate `phase1-runtime-validation/` application.

Read these current sources before execution:

| Source | Purpose |
| --- | --- |
| [README.md](README.md) | Project layout and entry points |
| [runbook.md](docs/phases/phase-01-runtime-validation/runbook.md) | Deployment, integration and reset procedures |
| [final report](docs/phases/phase-01-runtime-validation/verification-report.md) | Completed independent acceptance and exact test scope |
| [validation boundaries](docs/phases/phase-01-runtime-validation/verification-open-questions.md) | Capabilities not verified by Phase 1 |
| [evidence index](evidence/phase-01-runtime-validation/index.json) | Retained acceptance evidence and hashes |
| [latest captured environment](evidence/phase-01-runtime-validation/environment-current.json) | A timestamped snapshot, not a substitute for live readback |

Leave `ReasonFuse_Phase1_Runtime_Validation_Construction_Prompt.md` unchanged;
it is a historical construction instruction, not a new execution task.

Independent acceptance completed all four spikes, two full batches, deployed-source
identity, clean-start and final reset. Superseded reports and diagnostic attempts
were removed in an owner-authorized learning cleanup; do not reconstruct or review
them. For a future separately requested validation, apply all gates below to fresh
evidence rather than copying this dated PASS.

Keep the four frozen assumptions and all acceptance gates below. The implemented
Operations API is a deterministic external test service: DNS returns a controlled
result and restart records `SIMULATED_RESTART`. These tests prove invocation,
interception and approval behavior, not a restart of a production service.
The routing and SSE probes use normal Agent Framework middleware through real
Hosted Agent/APIM endpoints; they do not prove model-generated token streaming.

---

# 1. Mission

Your job is to verify whether the four architecture-critical runtime assumptions work in real execution.

You are NOT here to improve the architecture.

You are NOT here to expand the system.

You are NOT here to reward partial implementation.

You must execute the real integration paths, capture evidence, and return:

```text
Spike 1 — PASS / FAIL / NOT VERIFIED
Spike 2 — PASS / FAIL / NOT VERIFIED
Spike 3 — PASS / FAIL / NOT VERIFIED
Spike 4 — PASS / FAIL / NOT VERIFIED

Architecture Unfreeze Required? YES / NO

PHASE 1 RESULT:
PASS / BLOCKED
```

Phase 1 passes only if:

```text
4 / 4 spikes PASS
AND clean-start revalidation PASS
AND evidence is tied to the source revision actually deployed
```

During execution, use `NOT VERIFIED` for an unexecuted or unevidenced requirement.
At final closeout, an incomplete critical requirement means
`PHASE 1 RESULT: BLOCKED`; distinguish missing evidence from an observed runtime FAIL.

---

# 2. Validation Principles

## Principle 1 — Trust Execution, Not Claims

Do not accept:

```text
"the code looks correct"
"the SDK should support this"
"the docs say this is valid"
"unit tests pass"
"Terraform plan succeeds"
```

as proof of a spike.

Require real execution evidence.

---

## Principle 2 — Do Not Fix Failures Silently

If a spike fails:

```text
preserve evidence
identify the failing assumption
mark FAIL
```

You may make small diagnostic changes, but do not redesign the system and then pretend the original architecture passed.

Record every diagnostic or corrective change, its source diff, and the versions
tested before and after it. Preserve the failed run. A correction requires fresh
affected tests and the full clean-start revalidation before final PASS.

---

## Principle 3 — Distinguish Implementation Bug from Architecture Failure

Classify every failure as one of:

```text
IMPLEMENTATION_BUG
CONFIGURATION_ERROR
ENVIRONMENT_ERROR
SDK_VERSION_INCOMPATIBILITY
ARCHITECTURE_ASSUMPTION_FAILURE
```

Only the last category automatically triggers:

```text
Architecture Unfreeze Required = YES
```

Use this classification consistently in all spike sections. A missing deployment,
missing evidence, configuration error or implementation bug is not by itself proof
that a frozen architecture assumption failed. `Unfreeze = NO` while validation is
blocked means no demonstrated need to unfreeze; it does not mean acceptance passed.

---

# 3. Pre-Validation Environment Audit

Before validating spikes, record:

```text
date/time in UTC
Git commit, working-tree status, and any diagnostic diff
Azure subscription / Foundry project
region (Australia East / australiaeast)
Hosted Agent names, versions, status, code content_hash and entry point
Toolbox version
model deployment name, model version, SKU and capacity
APIM endpoint

local and hosted Python versions
agent-framework-core version
agent-framework-foundry version
agent-framework-foundry-hosting version
azure-ai-projects version
azure-identity version
azure-ai-agentserver-responses version

azd version
azd agent / project / toolbox extension versions
uv version
terraform version
azurerm provider version
azapi provider version
```

At construction handoff the subscription was
`7c73b89d-485e-43a9-8d66-b12b766d567f`, resource group
`rg-reasonfuse-phase1-aue`, and Foundry project `reasonfuse-phase1`.
The snapshot recorded stable v4, candidate v1, and Toolbox v2. Re-read live state;
do not hard-code these versions as the expected result of a later deployment.
Existing Azure names retain their phase suffix; the repository move does not
authorize renaming or recreating cloud resources.

Use `pyproject.toml`, `uv.lock`, `requirements.txt`, `scripts/bootstrap.ps1` and
`infra/.terraform.lock.hcl` as the pinned baseline. The implementation intentionally
installs `agent-framework-core` rather than the all-integrations `agent-framework`
umbrella package. Do not install Full Harness or upgrade dependencies to perform
this validation.

Check exact dependency pins and frozen export consistency. Record SHA-256 hashes
of the dependency files and capture actual tool versions. In particular,
`scripts/capture_environment.py` currently labels CLI/provider versions with
configured constants; verify those fields against executable version output and
the installed provider selections. Its hosted-agent readback alone is not a
complete subscription, model, Toolbox, APIM or local-tool audit.

The source under test must match the code deployed to both release backends.
Record the deployment command, source revision, dependency hashes, service-to-agent
mapping, returned agent versions and uploaded `content_hash`. A content hash from
an older environment snapshot does not establish that the current tree was deployed.
If the mapping is unavailable or stale, deploy the intended revision using the
runbook before claiming a current-source result.

Use PowerShell 7 on Windows. Bootstrap the pinned tooling if needed, then run:

```powershell
Set-Location -LiteralPath 'D:\workshop\sep\reason-fuse'
pwsh -File scripts/bootstrap.ps1
uv sync --frozen --python 3.13
pwsh -File scripts/preflight.ps1
.venv/Scripts/python.exe scripts/capture_environment.py
```

Execute each command separately, capture its exit code, and stop on failure.
The `.sh` wrappers delegate to PowerShell and are not independent Linux support.
Do not print `.azure` environment files, credentials or Terraform state.

Existing integration entry points are listed below. Run them sequentially because
the external counters are shared. Run both Toolbox cases at least twice per batch.
Record each invocation separately; a script's exit code does not replace review
of the acceptance checks in Sections 4–7.

```powershell
.venv/Scripts/python.exe tests/integration/history_session.py
.venv/Scripts/python.exe tests/integration/toolbox_interception.py allow
.venv/Scripts/python.exe tests/integration/toolbox_interception.py block
.venv/Scripts/python.exe tests/integration/toolbox_interception.py allow
.venv/Scripts/python.exe tests/integration/toolbox_interception.py block
.venv/Scripts/python.exe tests/integration/approval.py approve
.venv/Scripts/python.exe tests/integration/approval.py deny
.venv/Scripts/python.exe tests/integration/approval.py binding
.venv/Scripts/python.exe tests/integration/apim.py affinity
.venv/Scripts/python.exe tests/integration/apim.py new_session_control --samples 60
.venv/Scripts/python.exe tests/integration/apim.py sse
.venv/Scripts/python.exe scripts/capture_telemetry.py
```

The minimum suite includes additional evidence review for duplicate history,
approval replay/denial, release-to-weight mapping and SSE event ordering. Add
small diagnostic client checks where the existing scripts do not establish a
requirement; preserve their code and output with the validation evidence.

If preflight fails because the environment is not deployable, Phase 1 cannot PASS.

Explain doctor skips individually. SDK-managed Toolbox checks skipped by doctor
must be covered by the real Toolbox smoke and integration paths, not counted as
automatically passing.

---

# 4. Spike 1 Validation — Responses History + AgentSession

## Frozen Assumption

```text
Foundry Agent Server
=
canonical conversation-history owner

AgentSession
=
runtime/provider/ReasonFuse state owner
```

Required host configuration:

```text
ResponsesHostServer(
    history_source="agent_server"
)
```

Required downstream behavior:

```text
store = false
```

Distinguish the two API layers: the client calls Foundry's canonical conversation
and Responses endpoints with `store=True`; the agent's downstream model client
uses `store=False`. These are compatible ownership settings.
Current entry points are `src/main.py`, `src/reasonfuse/main.py` and
`src/reasonfuse/agent.py`; state restoration lives under
`src/reasonfuse/validation/`.

---

## Test A — Multi-Turn History

Start a new conversation.

Turn 1:

```text
My service is unhealthy.
Remember incident ID INC-001.
```

Record:

```text
conversation_id
platform agent_session_id from the Hosted response
framework AgentSession ID from read_runtime_state
response
```

These identifiers have different owners; do not require all three values to be
equal. Require each relevant identifier to remain consistent across the same
conversation's turns.

Turn 2, same conversation:

```text
What incident ID are we investigating?
```

Expected:

```text
INC-001
```

---

## Test B — AgentSession State

Before or during Turn 1, ensure:

```text
reasonfuse_test_state = "RF-STATE-001"
```

is stored in AgentSession state.

After Turn 2, verify:

```text
reasonfuse_test_state == "RF-STATE-001"
```

using runtime/session evidence, not an LLM-generated statement.

Inspect the actual `read_runtime_state` function output via the existing
`runtime_state()` helper. A constant marker alone can be reinitialized and is
insufficient proof of restoration. Require the same framework session ID, turn
number progressing from 1 to 2, and `restored_at_turn_start` changing from false
to true. Capture the reported provider state and input counts.

---

## Test C — Duplicate History Detection

Inspect available logs/traces/message counts.

Look for:

```text
duplicate user message
duplicate assistant message
duplicate tool call
replayed transcript
duplicate continuation
```

There must be no evidence that a second HistoryProvider reloads the same canonical conversation.

Inspect actual turn inputs and canonical conversation items/tool events, using
unique turn markers or equivalent trace evidence. Explain legitimate tool-loop
messages rather than assuming a fixed input count. The current history script
does not by itself exhaustively prove absence of duplicate replay.
The hosting SDK may install a non-loading history sentinel; the presence of a
provider object alone is not a second canonical-history load. If available
instrumentation cannot distinguish the two, mark this requirement NOT VERIFIED.

---

## Spike 1 PASS Criteria

All must be true:

```text
[ ] Turn 2 remembers INC-001
[ ] Foundry conversation is the canonical transcript
[ ] AgentSession preserves RF-STATE-001
[ ] store=False is active
[ ] no duplicate history is observed
[ ] no custom canonical history store is required
```

If any frozen ownership assumption fails in real execution:

```text
Spike 1 = FAIL
Architecture Unfreeze Required = YES
```

---

# 5. Spike 2 Validation — Local Toolbox Interception

## Frozen Assumption

Every ReasonFuse-critical tool can execute through:

```text
Agent Framework
 ↓
Function Calling Middleware
 ↓
Local Tool / MCP Invocation
 ↓
Foundry Toolbox
```

and can be intercepted before execution.

This is the most important Phase 1 spike.

The conceptual tool names below map to the current `tools/list` schema:

```text
operations___dns_resolution    {"body": {"hostname": "..."}}
operations___restart_service   {"body": {"service_name": "..."}}
```

Capture the live names/schema and the middleware's actual argument objects.
Flat conceptual signatures in the examples are not the native wire payload.
Approval modes are attached by the local `FoundryToolbox` integration in
`src/reasonfuse/agent.py`: DNS `never_require`, restart `always_require`.
Toolbox metadata alone is not evidence that runtime approval is enforced.

Use the independently hosted Operations API counters through the existing
`Operations` helper. Record the counter epoch and before/after values for every
allow, block and approval case. An epoch change or service restart within a proof
interval invalidates the counter comparison. Never reset counters between an
action and its after-check, and never run counter-based cases concurrently.

---

## Test A — Allow Path

Call:

```text
dns_resolution("api.reasonfuse.local")
```

Capture logs.

Required observable order:

```text
BEFORE dns_resolution
TOOL EXECUTED
AFTER dns_resolution
```

Confirm BEFORE sees:

```text
tool name
arguments
```

Confirm AFTER sees:

```text
tool result
```

Require exactly one external DNS invocation in the same counter epoch and an
AFTER result corresponding to that invocation. Record actual middleware events
from runtime/provider state, not text generated by the model.

---

## Test B — Block Path

Call:

```text
dns_resolution("blocked.reasonfuse.local")
```

Required:

```text
BEFORE
BLOCK
```

Forbidden:

```text
TOOL EXECUTED
AFTER with a real external result
```

Use an external/tool execution counter or equivalent evidence.

Required:

```text
execution_count delta = 0
```

Do not accept middleware logs alone if the tool could still have executed.

---

## Test C — Repeatability

Run Allow and Block tests more than once.

Confirm behavior is deterministic.

Use at least two fresh allow runs and two fresh block runs in each validation
batch. Preserve all attempts, including failures; a later success does not erase
an earlier failure.

---

## Spike 2 PASS Criteria

```text
[ ] BEFORE observes tool name
[ ] BEFORE observes args
[ ] allowed call executes
[ ] AFTER observes result
[ ] blocked call never executes externally
[ ] block decision is made before execution
[ ] path uses local Agent Framework invocation
[ ] Foundry Toolbox remains the managed tool surface
```

If Foundry Toolbox critical calls cannot be intercepted before execution using the selected supported local integration:

```text
Spike 2 = FAIL
Architecture Unfreeze Required = YES
```

---

# 6. Spike 3 Validation — R2 Human Approval Round-trip

## Frozen Assumption

A high-impact tool can:

```text
pause before execution
→ request approval
→ preserve AgentSession state
→ resume exact action
→ execute once
```

---

## Test A — Approval Pause

Drive the native `mcp_approval_request` / `mcp_approval_response` flow. Capture
the approval ID, tool name, exact parsed arguments, conversation and session IDs.
A user message saying "yes" is not the protocol approval response.

Set:

```text
reasonfuse_test_counter = 7
```

Request:

```text
restart_service("orders")
```

Before approval:

```text
tool execution count must remain 0
```

---

## Test B — Approve Exact Action

Approve:

```text
restart_service("orders")
```

Required:

```text
tool executes exactly once
```

After execution confirm:

```text
reasonfuse_test_counter == 7
```

Also require the same framework AgentSession ID and restored state after resume.
The counter is initialized with `setdefault`; seeing the number 7 alone does not
prove that a paused session was restored.

---

## Test C — Denial

Request:

```text
restart_service("payments")
```

Deny.

Required:

```text
tool execution count delta = 0
```

The current `approval.py deny` case denies `orders`. The `binding` case also
requests and denies `payments`; inspect its fresh payments approval and unchanged
external counters to cover this test. Do not label the standalone deny case as a
payments test. If binding exits before the payments denial, run a supplemental
native denial check and preserve its evidence.

---

## Test D — Approval Binding

Approve only:

```text
restart_service("orders")
```

Then attempt:

```text
restart_service("payments")
```

without a new approval.

Required:

```text
payments action does not execute
```

---

## Test E — One-Time Consumption

Try to replay the same approval if the framework exposes a replay path.

Required:

```text
no duplicate side effect
```

The existing binding case reuses the consumed orders approval while requesting
payments. Require orders to remain at one execution and payments at zero, with
a different approval ID for payments. A genuine native replay rejection such as
HTTP 400/409/422 is acceptable only when its error evidence and unchanged external
counters are recorded. Do not treat an unrelated transport failure as safe replay.
If exact same-action replay is supported, exercise it as well; otherwise document
the unsupported path and the one-time-consumption coverage actually observed.

---

## Spike 3 PASS Criteria

```text
[ ] R2 pauses before execution
[ ] approve resumes exact action
[ ] approved action executes once
[ ] deny prevents execution
[ ] AgentSession state survives round-trip
[ ] approval is bound to exact args
[ ] approval cannot silently authorize another action
```

If runtime approval cannot safely preserve/restore the required state:

```text
Spike 3 = FAIL
Architecture Unfreeze Required = YES
```

---

# 7. Spike 4 Validation — APIM Sticky Canary + SSE

## Frozen Assumption

APIM can provide:

```text
weighted Stable/Candidate routing
+
sticky release affinity
+
unbuffered Responses streaming
```

---

# 7A. Sticky Canary Validation

Confirm backend configuration:

```text
Stable weight    = 95
Candidate weight = 5
session affinity = ON
```

Read back the active native APIM backend pool and effective API policy. Map each
backend ID/URL to its actual stable or candidate version and weight; checking
only an unordered pair of weights is insufficient. Preserve the mapping alongside
the live release probes. The current cookie name is `ReasonFuseAffinity`.

Use one persistent HTTP client/session.

Perform:

```text
Turn 1
Turn 2
Turn 3
Turn 4
Turn 5
```

Record:

```text
release_role
affinity cookie/header state
request ID
```

Expected:

```text
all five turns use the same release backend
```

Example valid:

```text
Candidate
Candidate
Candidate
Candidate
Candidate
```

Example invalid:

```text
Candidate
Stable
Candidate
Stable
```

---

## Negative Control

Create a brand-new HTTP client/session.

Do not reuse the previous affinity state.

Confirm it can independently receive a release assignment.

Use a fixed initial cohort of 60 fresh clients with empty cookie jars. Preserve
all assignments, both backend counts and the existing 99% Wilson interval.
Combined with active pool/policy readback, observing both backends supports
independent routing and checks consistency with the configured 5% candidate
weight. It does not establish an exact observed 95/5 ratio or, by itself, prove
that the cookie is the only cause of stickiness.

Zero candidate assignments in a finite cohort can occur by chance. Preserve the
script failure and investigate before classifying it. If additional sampling is
needed, declare its fixed size before running it, retain both cohorts, and report
all observations. Do not rerun until a favorable sample appears. Insufficient
evidence keeps this requirement NOT VERIFIED and blocks final PASS; it is not
automatically an architecture failure.

---

# 7B. SSE Streaming Validation

Call an endpoint that emits:

```text
chunk-1
chunk-2
chunk-3
chunk-4
```

Capture client receive timestamps.

Required:

```text
chunk-1 arrives before final completion
chunk-2 arrives before final completion
chunk-3 arrives before final completion
```

Verify APIM configuration:

```text
buffer-response = false
response caching = OFF
streaming body diagnostics = OFF
```

Use the real `RF_SSE_PROBE` Hosted/APIM path. It emits four updates approximately
0.75 seconds apart from deterministic Agent Framework middleware. The existing
script checks a span of at least 1.5 seconds and adjacent gaps of at least
0.35 seconds. Independently inspect `SSE_EVENT` records to confirm chunks 1–3
arrive before the terminal `response.completed` event, and no error/failure event
occurs. Record client monotonic receive times; total first-token latency is not
the buffering criterion. This validates transport streaming, not model inference.

Inspect effective policy for inherited buffering, caching or body inspection.
Verify all four APIM diagnostic request/response body limits are zero and
sensitive header capture is disabled. Keep metadata diagnostics enabled:
capture recent real APIM request telemetry with `scripts/capture_telemetry.py`.
Ingestion delay must be recorded and checked again; an enabled diagnostic setting
without ingested records is not proof of runtime telemetry.

Do not accept one complete payload split locally after receipt.

---

## Spike 4 PASS Criteria

```text
[ ] weighted pool is active
[ ] affinity state is issued/preserved
[ ] same client stays on one backend
[ ] new client can be assigned independently
[ ] SSE chunks arrive incrementally
[ ] APIM does not buffer complete response
```

If APIM cannot preserve the required release affinity for the chosen client flow:

```text
Spike 4 = FAIL
Architecture Unfreeze Required = YES
```

---

# 8. Clean-Start Validation

After individual spikes and their supplementary checks pass, run a second,
separately identified validation batch:

1. Preserve the first batch, source revision, dependency hashes and environment
   readback. Stop test clients and reset recorded hosted test sessions and external
   counters with `pwsh -File scripts/reset.ps1`. Inspect its actual result.
2. Recreate a fresh local Python 3.13 `.venv` at the repository root and restore
   dependencies with `uv sync --frozen --python 3.13`. Keep the prior environment
   locally if needed for diagnosis. Record how the fresh environment was created.
3. Restore/check pinned tooling with `pwsh -File scripts/bootstrap.ps1`.
   Preserve the existing ignored `.azure` configuration and authoritative Terraform
   state. They are deployment ownership data, not disposable test state. On a
   different machine, recover that state through the documented secure handoff
   before deployment; do not provision over existing resources from empty state.
4. Deploy the recorded source revision with `pwsh -File scripts/deploy.ps1`,
   without `-DnsOnly`. Capture exit status and verify both active agent versions,
   code hashes, dependencies, Toolbox and APIM mappings. A tool-version check or
   a Terraform plan is not this deployment step.
5. Run `pwsh -File scripts/preflight.ps1`, then capture the environment again.
   Use fresh conversations, sessions, approvals and HTTP cookie jars. Rerun every
   command in the Section 3 integration sequence and all supplementary acceptance
   checks, including repeated allow/block cases and telemetry evidence.
6. After evidence capture, run `pwsh -File scripts/reset.ps1` again and verify
   cleanup. Record all recorded-session deletion outcomes and zero external
   counters. Foundry may retain session metadata with explicit `deleted` status;
   accept absent or `deleted`, not other states.

The current reset script scans nested evidence paths and deletes only recorded
hosted test sessions; it does not destroy infrastructure. Reset alone is not
clean-start validation. This gate requires a fresh local dependency environment,
documented deployment and a fresh complete integration batch.

A full resource-group teardown is not required for this gate. Preserve resource
names and Terraform ownership; never destroy shared resources to simulate a fresh
client. If deployment or the second complete batch cannot be executed, report
clean-start `NOT VERIFIED` and Phase 1 `BLOCKED`.

---

# 9. Evidence Requirements

For every PASS claim, capture:

```text
command
timestamp
exit code
relevant logs
trace/request IDs where available
conversation/session IDs
execution counters
HTTP affinity evidence
stream timestamps
package versions
source/deployment identity and dependency file hashes
counter epochs and per-action deltas
initial versus clean-start batch identity
```

Existing helpers write new JSONL files under
`evidence/phase-01-runtime-validation/runs/<UTC-date>/`.
Create a separate
`evidence/phase-01-runtime-validation/verification-<UTC-timestamp>/index.json`
mapping each requirement and batch to repo-relative evidence paths, SHA-256
hashes and outcomes. During a new validation, keep diagnostic scripts and sanitized
logs with that batch. Do not overwrite the retained completed acceptance evidence.
This does not require restoring artifacts removed by the owner after closeout.

`environment-current.json` is a rolling snapshot. Preserve each validation
batch's timestamped environment output and all required supplementary live
readback before a later capture replaces that snapshot.

Do not expose:

```text
tokens
passwords
secrets
connection strings
raw bearer/affinity cookie values
```

Redact sensitive values before publishing evidence. Use cookie names, issuance
and persistence observations, and hashes where needed. Do not publish Terraform
state or plans, `.azure` files or an unfiltered environment dump.

---

# 10. Validation Report

Create or update the independent report:

```text
docs/phases/phase-01-runtime-validation/verification-report.md
```

For a future separately requested validation, use the structure below and link
every result to its new evidence index. Do not recreate the removed construction
report or reopen the closed historical investigation.

```text
# Phase 1 Independent Runtime Validation Report

## Environment
...

## Source and Deployment Identity
Git revision / diagnostic diff:
Dependency hashes:
Stable / candidate versions and content hashes:
Live Toolbox / model / APIM mapping:
Initial and clean-start evidence indexes:

## Spike 1 — Responses History + AgentSession
Status: PASS / FAIL / NOT VERIFIED
Evidence:
...
Failure Classification:
...

## Spike 2 — Local Toolbox Interception
Status: PASS / FAIL / NOT VERIFIED
Evidence:
...
Failure Classification:
...

## Spike 3 — R2 Human Approval
Status: PASS / FAIL / NOT VERIFIED
Evidence:
...
Failure Classification:
...

## Spike 4 — APIM Sticky Canary + SSE
Status: PASS / FAIL / NOT VERIFIED
Evidence:
...
Failure Classification:
...

## Clean-Start Revalidation
Status: PASS / FAIL / NOT VERIFIED
Fresh environment and deployment evidence:
All four spikes and supplementary checks:
Final cleanup:

## Coverage and Limits
Requirement-by-requirement evidence, skipped checks and explanations:
Observed failures and all corrective changes:
Mock operations / deterministic transport-probe boundaries:

## Architecture Unfreeze Required?
YES / NO

Reason:
...

## Phase 1 Result
PASS / BLOCKED
```

---

# 11. Final Decision Rules

## PASS

Only return:

```text
PHASE 1 RESULT: PASS
```

when:

```text
Spike 1 PASS
AND
Spike 2 PASS
AND
Spike 3 PASS
AND
Spike 4 PASS
AND
clean-start revalidation PASS
AND
both batches are tied to the intended deployed source and dependencies
AND
every critical requirement has fresh evidence (none NOT VERIFIED)
```

---

## BLOCKED

Return:

```text
PHASE 1 RESULT: BLOCKED
```

if any critical spike fails after reasonable diagnostic work, or any mandatory
audit, deployment-identity, evidence or clean-start requirement remains unverified.

Do not weaken the acceptance criteria to obtain a PASS.

---

# 12. Final Validator Instruction

Your job is to falsify the architecture assumptions if they are wrong.

Do not optimize for making the project look successful.

Optimize for certainty.

The most valuable Phase 1 result is either:

```text
4 / 4 PASS + clean-start PASS + complete deployment/evidence mapping
→ the four Phase 1 runtime assumptions are validated within the stated test scope
→ proceed to Phase 2
```

or:

```text
a precise FAIL or documented missing evidence
→ blocking cause and failure classification identified
→ evidence preserved
→ Phase 2 avoided until corrected
```

Never return PASS because the implementation appears plausible.
