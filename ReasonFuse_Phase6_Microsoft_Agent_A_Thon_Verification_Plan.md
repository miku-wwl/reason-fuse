# ReasonFuse Phase 6 — Microsoft Agent-a-thon Verification Plan

> **Phase:** 6  
> **Target:** Microsoft Agent-a-thon submission version  
> **Companion document:** `ReasonFuse_Phase6_Microsoft_Agent_A_Thon_Construction_Plan.md`  
> **Verification scope:** Local correctness → curated Azure E2E → evidence capture → OFF/ON comparison → claim audit → final submission gate  
> **Core rule:** **Verification proves the frozen design. It does not create a new design.**  
> **Phase 7:** 1010 competition verification is separate and will add formal Skill-package acceptance criteria.

## Current execution snapshot — 2026-09-13

The current repository has completed the local construction evidence described
by this plan: 36 unit/boundary tests, local wiring/history audits, compileall,
the 15-scenario matrix, Terraform static checks, the resettable Operations
fixture HTTP smoke, and a bounded local OFF/ON comparison all pass. The
consolidated record is
`ReasonFuse_PHASE6_MICROSOFT_SUBMISSION_EVIDENCE.md`.

The retained bounded Hosted Agent/multi-turn/containment result is a prior
local-only Azure audit claim. Native approval, cloud Operations outcome
verification, Application Insights export, Toolbox/IQ, APIM live behavior, and
the final video remain `NOT VERIFIED` or pending. This plan continues to define
the required acceptance gates; the snapshot is not a substitute for missing
cloud evidence.

---

# 0. Purpose

This document defines **how Phase 6 is proven complete**.

The construction document answers:

> What should be built or polished for the Microsoft submission?

This verification document answers:

> What evidence is required before we are allowed to claim that each part works?

The verification standard is intentionally **hackathon-grade but correctness-strict**.

We do **not** need:

```text
production certification
large load testing
hundreds of repeated model runs
formal SLO qualification
multi-region failover
production HA certification
large benchmark infrastructure
```

We **do** need:

```text
local deterministic correctness
truthful cloud integration proof
real native approval proof
real outcome-verification proof
real containment proof
inspectable telemetry
small OFF vs ON evidence
claim-to-evidence traceability
```

---

# 1. Verification Philosophy

Use the cheapest trustworthy proof first.

```text
Static / local proof
        ↓
Deterministic scenario proof
        ↓
Infrastructure proof
        ↓
Small curated Azure E2E proof
        ↓
Submission evidence
```

Do not spend Azure budget proving something already proven better by deterministic local tests.

Cloud runs are reserved for claims that require a real Microsoft runtime, including:

```text
Foundry Hosted Agent
Responses 2.0.0 hosting
native runtime approval
real hosted session/state behavior
Application Insights export
real Toolbox / Foundry IQ integration when used
APIM behavior when included as live evidence
```

---

# 2. Evidence Status Vocabulary

Every Phase 6 claim must use one of these statuses.

## PASS

The expected behavior was executed and captured with sufficient evidence.

## FAIL

The behavior executed but violated the expected contract.

## NOT VERIFIED

The behavior was not executed, could not be observed, or evidence is insufficient.

## BLOCKED

Execution could not proceed because of an external dependency such as:

```text
quota
permissions
Azure resource availability
SDK/API outage
deployment boundary not yet implemented
```

## OPTIONAL NOT RUN

Only valid for explicit P0.5 items.

Never turn:

```text
BLOCKED
NOT VERIFIED
OPTIONAL NOT RUN
```

into:

```text
PASS
```

in README, presentation, demo narration, or final submission text.

---

# 3. Evidence Strength Levels

Use these labels in reports.

## L0 — Design / Code Evidence

Example:

```text
approval_mode declares restart_service as approval-required
```

This proves implementation intent only.

It does **not** prove Azure runtime behavior.

---

## L1 — Local Execution Evidence

Example:

```text
unit test verifies stale generation => OUTCOME_UNKNOWN
```

This proves deterministic behavior locally.

It does not prove Hosted Agent integration.

---

## L2 — Hosted Integration Evidence

Example:

```text
Foundry Hosted Agent generates native approval request
and restart_service has not executed yet
```

This proves the Microsoft integration path.

---

## L3 — End-to-End Competition Evidence

Example:

```text
live Hosted Agent
→ native approval
→ accepted restart
→ fresh world-state read
→ OUTCOME_VERIFIED
→ telemetry visible in Application Insights
```

This is the strongest Phase 6 evidence.

---

# 4. Phase 6 Verification Gates

Phase 6 uses these gates:

```text
V0  Source / Environment Baseline
V1  Local Core Regression
V2  15-Scenario Behavioral Verification
V3  Infrastructure Static Verification
V4  Azure Provision + Hosted Deployment Smoke
V5  Hosted Runtime / Session-State Verification
V6  Live Deterministic Containment
V7  Native Approval + Outcome Verification
V8  Telemetry / Application Insights Verification
V9  Microsoft Integration Extras
V10 OFF vs ON Comparative Evidence
V11 Submission Claim Audit
V12 Cleanup / Final Freeze
```

P0 submission requires:

```text
V0–V8
V10–V12
```

V9 contains optional integrations that must not block the core submission unless the final presentation explicitly depends on them.

---

# 5. V0 — Source / Environment Baseline

## Goal

Prove we know exactly what version is being tested.

## Required record

Capture:

```text
verification timestamp
git commit SHA
git branch
git status
Python version
uv version
Terraform version
az CLI version
azd version
installed azd extension versions
Azure subscription name/id masked as needed
target region
```

## Repository baseline commands

From repository root:

```powershell
git rev-parse HEAD
git branch --show-current
git status --short

python --version
uv --version
terraform version
az version

pwsh -File scripts/bootstrap.ps1
uv sync --frozen --python 3.13
```

Expected pinned deployment tooling from the current repository:

```text
Python: 3.13
azd: 1.33.0
azure.ai.agents extension: 1.0.0-beta.13
azure.ai.projects extension: 1.0.0-beta.9
azure.ai.toolboxes extension: 1.0.0-beta.6
```

Current Python dependencies are pinned through `pyproject.toml` / `uv.lock`.

## PASS

```text
working tree understood
tool versions captured
required tools available
dependency installation succeeds
```

A dirty working tree is not automatically FAIL, but every dirty file must be explained before final submission.

---

# 6. V1 — Local Core Regression

## Goal

Verify that Phase 6 work has not damaged the frozen ReasonFuse core.

## Setup

```powershell
uv sync --frozen --python 3.13
$env:PYTHONPATH = (Join-Path $PWD 'src')
```

## Required commands

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p 'test*.py'
.venv/Scripts/python.exe tests/local_wiring.py
.venv/Scripts/python.exe tests/local_history_audit.py
.venv/Scripts/python.exe -m compileall -q src tests server.py
git diff --check
```

## Expected local probes

`local_wiring.py` should end with:

```text
LOCAL_WIRING_PASS (not hosted integration validation)
```

`local_history_audit.py` should end with:

```text
LOCAL_HISTORY_AUDIT_PASS (observation-only; not hosted acceptance)
```

These exact warnings matter.

They prevent us from falsely describing local middleware proof as Azure Hosted proof.

## PASS

All commands succeed.

## FAIL examples

```text
unit test regression
middleware local probe executes a blocked tool
history audit mutates supplied history
store=False contract is altered
compile failure
whitespace / patch corruption from git diff --check
```

---

# 7. V2 — 15-Scenario Behavioral Verification

## Goal

Re-run the lightweight deterministic behavior matrix after Phase 6 engineering changes.

Source of truth:

```text
benchmark/15-scenarios.md
```

Each scenario runs **once** unless a failure requires debugging.

Do not convert debugging retries into benchmark repetitions.

---

## Required scenario set

### Healthy

```text
H-001
H-007
H-010
```

### Planning / No Progress

```text
NP-001
```

### Exact Loop

```text
EL-001
EL-005
EL-009
```

### Oscillation

```text
OS-001
OS-007
OS-012
```

### Retrieval Churn

```text
RC-001
RC-010
RC-020
```

### Outcome Failure / Unknown

```text
OF-001
OF-002
```

---

## Important observation-contract rule

Detector-focused local scenarios may use the documented focused observation contract, e.g.:

```text
max_stalled_steps=10
required_objective_progress_interval=10
```

If an override is used:

```text
record it
```

Never describe the override as the default Hosted Agent contract.

The current default `RunContract` is:

```text
max_steps = 12
max_tool_calls = 10
max_stalled_steps = 2
max_oscillation_cycles = 2
max_retrieval_churn = 3
max_side_effects = 1
required_objective_progress_interval = 2
require_postcondition_for_side_effects = true
version = reasonfuse-contract-v1
```

---

## Required result template

```markdown
### <SCENARIO_ID> — <category>

- Timestamp:
- Commit:
- Environment:
- State reset:
- Contract / override:
- Actual tool sequence:
- Actual detector / failure type:
- Actual outcome:
- Result: PASS / FAIL / NOT VERIFIED
- Evidence:
- Notes:
```

## PASS

All 15 scenarios have an explicit status.

P0 target:

```text
15 / 15 PASS
```

If one is FAIL:

```text
Phase 6 submission is blocked
```

unless the failing case is formally removed from project claims and the implementation/documents are updated accordingly.

---

# 8. V3 — Infrastructure Static Verification

## Goal

Verify Phase 6 infrastructure before spending Azure budget.

## Required checks

```powershell
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra validate
pwsh -File scripts/terraform_plan_safe.ps1
```

The current safe-plan script uses:

```text
-refresh=false
no apply
placeholder values when required
```

Its success marker is:

```text
TERRAFORM_PLAN_SAFE=PASS (refresh=false; no apply; no Azure resources changed)
```

The Phase 6 cleanup changed the script's local-only placeholders to
`rg-reasonfuse-phase6-plan`, `reasonfuse-phase6-plan`, and
`phase6-local-plan-only`. These are plan-only values, not deployed resource
identities.

---

## Static architecture checks

Verify that current infrastructure still declares:

```text
Foundry account/project
model deployment
Application Insights
Log Analytics
Operations Web App
APIM stable/candidate structure when retained
```

Verify that the deployment boundary remains:

```text
Terraform
→ infrastructure

azd hosted service deployment
→ src/main.py
→ stable / candidate agents
```

## PASS

```text
fmt PASS
validate PASS
safe plan PASS
no unintended destroy/replace surprise in reviewed plan
```

---

# 9. V4 — Azure Provision + Hosted Deployment Smoke

## Goal

Prove Phase 6 can create the required Microsoft environment and deploy the Hosted Agents.

This is the first cloud-costing gate.

Do not run before V0–V3 pass.

---

## Environment setup

```powershell
$azd = ".tools/azd-1.33.0/azd-windows-amd64.exe"
$envName = "<phase6-environment>"

& $azd auth login

# Choose exactly one:
& $azd env new $envName
# OR:
# & $azd env select $envName

& $azd env set AZURE_SUBSCRIPTION_ID "<subscription-id>"
& $azd env set AZURE_LOCATION "australiaeast"
& $azd env set PUBLISHER_EMAIL "<publisher-email>"
& $azd env set OPERATIONS_ADMIN_KEY "<secret>"
```

Do not write secrets into:

```text
README
azure.yaml
Terraform files
verification report
screenshots
presentation
```

---

## Provision

```powershell
& $azd provision --environment $envName --no-prompt
```

Expected infrastructure includes:

```text
resource group
Foundry account
Foundry project
model deployment
Application Insights
Log Analytics
Operations App Service resources
APIM resources if still enabled in infrastructure
```

The Operations App Service now has the matching repository source at
`server.py`; Terraform's `app_command_line` points to it. The current
`azure.yaml` deploy services are still only the two Hosted Agents, so a live
Operations code-delivery path must be verified separately and must not be
assumed from infrastructure creation alone.

---

## Hosted deployment

```powershell
& $azd deploy stable --environment $envName --no-prompt
& $azd deploy candidate --environment $envName --no-prompt
```

The current Hosted definition expects:

```text
protocol: responses
version: 2.0.0
Python 3.13
entryPoint: src/main.py
model: gpt-5-mini
```

The current logical Hosted Agent names are:

```text
reasonfuse-phase6-stable
reasonfuse-phase6-candidate
```

## PASS

```text
provision succeeds
stable deploy succeeds
candidate deploy succeeds
Hosted Agent can answer a smoke request
```

## Evidence

Capture:

```text
azd command result
Foundry agent identity/name
release role
deployment timestamp
one smoke request/response
```

Do not expose credentials.

---

# 10. V5 — Hosted Runtime / Session-State Verification

## Goal

Prove the actual Hosted runtime path used by the submission.

Current implementation requires:

```text
ResponsesHostServer(
    agent,
    history_source="agent_server"
)
```

and:

```text
default_options={"store": False}
```

ReasonFuse state is persisted through the Agent Framework context-provider / `AgentSession` path.

---

## V5-A — Runtime identity

Verify:

```text
Hosted Agent is executing deployed code
release_role is expected
Responses 2.0.0 path is active
```

Recommended proof:

```text
RF_RELEASE_PROBE
```

plus Hosted response / trace.

---

## V5-B — Multi-turn session continuity

Within one Hosted session:

```text
Turn 1
→ execute a controlled action
→ capture runtime state identifiers / counters

Turn 2
→ request exact runtime state
→ verify state continuity
```

Expected continuity candidates include:

```text
run_id where semantically expected
framework_session_id
agent_session_id
conversation_id
tool_call_count
recent_action_fingerprints
progress_history
contract version
```

Do not require fields to remain identical if the current runtime intentionally scopes them per run.

The check must follow actual implementation semantics, not assumptions.

---

## V5-C — History ownership / no duplicate transcript store

Prove Hosted behavior does not contradict:

```text
history_source="agent_server"
store=False
```

The local audit is L1 evidence.

The Hosted run should provide at least one L2 trace or runtime observation confirming the intended path without creating a second custom conversation history store.

## PASS

Hosted behavior is consistent with the repository's history-ownership claims.

---

# 11. V6 — Live Deterministic Containment

## Goal

Show a judge-facing failure trajectory that ReasonFuse stops for a deterministic reason.

Preferred live case:

```text
service_status
database_health
service_status
database_health
```

with no new objective evidence.

Alternative:

```text
same normalized diagnostic repeatedly
```

---

## Required setup

Use a contract that is:

```text
bounded
documented
small enough for demo
```

If the live demo uses non-default limits:

```text
record them explicitly
```

Do not silently tune until the demo passes.

---

## Required observed flow

```text
Agent proposes diagnostic
        ↓
Tool executes
        ↓
No meaningful objective progress
        ↓
Further equivalent / oscillating work proposed
        ↓
ReasonFuse detector trips
        ↓
state.contained = true
        ↓
fuse_reason set
        ↓
subsequent ordinary proposal is BLOCKED
```

---

## Evidence required

Capture:

```text
tool trajectory
tool_call_count
step_index
progress_state / last_signals
contained
fuse_reason
blocked proposal
REASONFUSE_FUSE_TRIPPED event
```

Expected failure type should match the trajectory, e.g.:

```text
EXACT_LOOP
OSCILLATING
RETRIEVAL_CHURN
NO_PROGRESS
BUDGET_EXHAUSTED
```

Do not accept:

```text
"it stopped eventually"
```

as PASS.

It must stop for the **expected deterministic reason**.

---

# 12. V7 — Native Approval + Outcome Verification

This is the most important Phase 6 E2E gate.

## Core thesis to prove

```text
tool proposal
≠ execution

accepted side effect
≠ verified success
```

---

# 12.1 V7-A — Native Approval Before Execution

## Goal

Prove `operations___restart_service` is controlled by the Microsoft Agent Framework native approval path.

Current agent configuration declares:

```text
always_require_approval:
    operations___restart_service
```

and diagnostic/read tools as never-require.

That code is only L0 evidence.

Phase 6 needs L2/L3 runtime proof.

---

## Required test

Start from a known reset world state.

Ask the Hosted Agent to perform a restart.

Expected:

```text
Agent submits restart_service tool proposal
        ↓
native approval request is emitted
        ↓
restart_service has NOT executed
```

Before approving, prove no side effect happened.

Preferred Operations-world evidence:

```text
restart call counter unchanged
generation unchanged
service state unchanged
no accepted restart record
```

The repository's local boundary is the dependency-free root `server.py` fixture,
aligned with Terraform's `python /home/site/wwwroot/server.py` command. It
supports `POST /v1/reset` with `verified`, `failed`, or `unknown` mode and
`POST /v1/restart_service` followed by `GET /v1/service_status`. That local
HTTP proof is L1 evidence; it must not be presented as Hosted Agent or Azure
Operations proof.

---

## Denial branch

Deny the approval once.

Expected:

```text
tool does not execute
world state does not change
approval cannot be reused
new action would require fresh approval
```

This branch is strongly recommended if cheap.

---

## Approval branch

Approve.

Expected:

```text
restart_service executes exactly once
side_effect_count increases as expected
tool returns accepted result
pending postcondition is created
```

PASS requires evidence that execution occurred **after**, not before, approval.

---

# 12.2 V7-B — Accepted Does Not Equal Verified

After approved restart:

```text
restart_service
→ accepted
```

ReasonFuse must not immediately claim:

```text
OUTCOME_VERIFIED
```

Expected intermediate state:

```text
pending_postcondition != null
verification reserve / required verification semantics active
```

This is a core competition claim.

---

# 12.3 V7-C — Successful Fresh Verification

Required flow:

```text
restart accepted
        ↓
fresh service_status
        ↓
resource identity matches
generation is newer / fresh
status satisfies postcondition
        ↓
OUTCOME_VERIFIED
```

Expected final state:

```text
last_postcondition_result.outcome = OUTCOME_VERIFIED
pending_postcondition cleared / resolved per implementation
progress reflects verified result
```

Use the same semantics represented locally by `H-001`.

---

# 12.4 V7-D — Failed Postcondition

Controlled Operations fixture:

```text
restart accepted
        ↓
fresh service_status = UNHEALTHY
```

Expected:

```text
POSTCONDITION_FAILED
```

Use the same semantics as:

```text
OF-001
```

The agent must not report healthy recovery.

---

# 12.5 V7-E — Outcome Unknown

Controlled fixture:

```text
restart accepted
        ↓
service_status is stale generation
```

Expected:

```text
OUTCOME_UNKNOWN
```

Use the same semantics as:

```text
OF-002
```

A stale or mismatched observation must never be treated as success.

---

## V7 PASS

Minimum P0 live proof:

```text
native approval request
no pre-approval execution
approved side effect
accepted != verified
fresh verifier read
OUTCOME_VERIFIED
```

Plus local proof of failed/unknown branches.

Ideal P0 live proof adds either:

```text
POSTCONDITION_FAILED
```

or:

```text
OUTCOME_UNKNOWN
```

as a second cloud signature run.

---

# 13. V8 — Telemetry / Application Insights Verification

## Goal

Prove a judge can inspect why ReasonFuse acted.

Current code emits ReasonFuse events including:

```text
REASONFUSE_TRACE_EXPORTER_READY
REASONFUSE_RUN_START
REASONFUSE_RUN_END
REASONFUSE_OBSERVATION
REASONFUSE_FUSE_TRIPPED
```

Important runtime attributes include:

```text
reasonfuse.fuse_reason
reasonfuse.failure_type
trajectory/progress signals
contract state
run/session identifiers
```

---

## Required telemetry runs

Capture telemetry for:

```text
one healthy / verified outcome run
one containment run
```

At minimum, show:

```text
REASONFUSE_OBSERVATION
REASONFUSE_FUSE_TRIPPED
```

where applicable.

---

## Evidence requirements

For the containment trace, be able to answer:

```text
Which tool was proposed?
What had happened before it?
Was objective progress detected?
Why did ReasonFuse stop?
Which run/contract did it belong to?
```

For the successful verification trace, be able to answer:

```text
Which side effect was accepted?
Which fresh observation verified it?
What was the final outcome?
```

---

## Security check

The current Hosted environment sets:

```text
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false
```

Verification must ensure evidence screenshots do not require or expose private prompt/message content.

Do not enable full message capture just to make the demo easier.

---

## PASS

Application Insights / Azure Monitor contains enough structured evidence to explain both:

```text
successful verified recovery
deterministic containment
```

If Application Insights was not deployed or queried, this gate is
`NOT VERIFIED`; local OTel/in-memory span evidence remains L1 only. Do not claim
that a cloud `REASONFUSE_FUSE_TRIPPED` event was captured without that resource
and a query result.

---

# 14. V9 — Microsoft Integration Extras

These are conditional.

They must not block the primary submission unless the final demo explicitly promises them.

---

# 14.1 Foundry Toolbox

If `TOOLBOX_ENDPOINT` is used in the final submission:

Verify one real call from Hosted Agent through Toolbox.

Evidence:

```text
tool name
Hosted invocation
returned deterministic result
ReasonFuse observation
```

PASS proves:

> Toolbox integration is genuine.

It does not need a large tool-suite benchmark.

---

# 14.2 Foundry IQ

If `FOUNDRY_IQ_MCP_ENDPOINT` is used in the final submission:

Verify:

```text
knowledge_base_retrieve
```

through the real Foundry IQ / Azure AI Search MCP boundary.

Evidence:

```text
real retrieved source/citation
ReasonFuse retrieval normalization
new retrieval evidence identity
```

Do not substitute the local `retrieval_fixture` and call it Foundry IQ.

If not live-proven:

```text
label it NOT VERIFIED / optional
```

---

# 14.3 APIM Sticky Canary

If APIM is shown as a live submission feature, verify:

```text
stable/candidate routing
95/5 backend configuration
session affinity
SSE pass-through
```

A minimal canary proof is enough.

If live APIM proof is unstable or expensive:

```text
retain infrastructure-as-code
describe it as deployment architecture
do not claim live canary validation
```

---

# 15. V10 — OFF vs ON Comparative Evidence

## Goal

Provide simple measurable evidence that ReasonFuse changes runtime behavior.

This is not a scientific performance benchmark.

It is a controlled competition comparison.

---

## 15.1 Experimental control

For every OFF vs ON pair, keep constant as far as practical:

```text
same scenario
same initial Operations state
same model deployment
same tool definitions
same prompt/goal
same contract except REASONFUSE_ENABLED
same deployment version
same region
```

Difference:

```text
REASONFUSE_ENABLED=false
vs
REASONFUSE_ENABLED=true
```

Record any unavoidable model nondeterminism as a limitation.

---

## 15.2 Comparison A — Unproductive trajectory

Preferred input:

```text
bounded diagnostic scenario designed to produce
repeat / oscillation / no-progress behavior
```

Capture:

```text
total tool calls
redundant/equivalent calls
containment step
final trajectory state
time to bounded stop
```

Do not claim latency improvement if network/model variance dominates.

---

## 15.3 Comparison B — False-success protection

Compare behavior around:

```text
restart accepted
```

Without ReasonFuse verification semantics:

```text
accepted response alone provides no proof of real recovery
```

With ReasonFuse:

```text
accepted
→ pending postcondition
→ fresh read
→ verified / failed / unknown
```

Preferred judge-facing metric:

```text
Verified Recovery:
OFF = not established
ON  = YES / NO / UNKNOWN based on fresh evidence
```

Avoid fabricating:

```text
"X% fewer incidents"
```

unless actually measured.

---

## 15.4 Final metric table

Final Phase 6 evidence should support a table like:

| Metric | ReasonFuse OFF | ReasonFuse ON |
|---|---:|---:|
| Tool calls | measured | measured |
| Redundant calls | measured | measured |
| Containment step | none / measured | measured |
| High-impact action gated | No | Yes |
| Fresh postcondition verification | No | Yes |
| Verified recovery | Not established | Verified / Failed / Unknown |
| Time to verified outcome | N/A / measured | measured |

Only populate cells supported by captured runs.

The current consolidated local evidence records the measured bounded pair:

```text
oscillating diagnostics: OFF 4 executed / 0 blocked; ON 3 executed / 1 blocked
accepted unhealthy restart: naive OFF 1 call with no verification; ON 2 calls → POSTCONDITION_FAILED
```

These are local deterministic controls, not cloud model-quality or latency
measurements.

---

# 16. V11 — Submission Claim Audit

## Goal

Ensure every sentence in README / presentation has evidence at the correct level.

Create a claim matrix.

Example:

| Claim | Required Evidence | Actual Status | Allowed Wording |
|---|---|---|---|
| ReasonFuse detects exact loops | local scenarios/tests | PASS | “detects” |
| ReasonFuse runs in Foundry Hosted Agent | Hosted deployment trace | PASS | “runs in” |
| native approval gates restart | live approval flow | LOCAL PASS / CLOUD E2E NOT VERIFIED | “native approval is configured; cloud gate is not yet proven” |
| side effects are postcondition-verified | live verification | LOCAL PASS / CLOUD E2E NOT VERIFIED | “core verifies postconditions locally; cloud proof is not yet verified” |
| Foundry IQ integrated | live IQ call | NOT VERIFIED | “designed to integrate” only |
| APIM sticky canary validated | live APIM test | NOT VERIFIED | “IaC includes” only |
| production-ready | production certification | NOT DONE | **do not claim** |

---

## Forbidden claim inflation

Do not use:

```text
production proven
enterprise production certified
zero false positives
guarantees safety
guarantees recovery
fully autonomous incident resolution
cost reduction of X%
MTTR reduction of X%
```

unless Phase 6 evidence really supports it.

Preferred wording:

```text
controlled E2E demonstration
hackathon-grade engineering proof
deterministic containment
verified postcondition
measured in our controlled scenario
```

---

# 17. V12 — Cleanup / Final Freeze

## Goal

Finish with a reproducible submission and no unnecessary cloud residue.

---

## Final repository checks

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p 'test*.py'
.venv/Scripts/python.exe tests/local_wiring.py
.venv/Scripts/python.exe tests/local_history_audit.py
.venv/Scripts/python.exe -m compileall -q src tests server.py
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra validate
git diff --check
git status --short
```

Also verify the consolidated evidence links resolve locally and that no
required `build_identity.json`, Azure report, Terraform state, or private
evidence file is being referenced as a tracked submission asset.

Run the final 15 scenarios if any core or detector-related code changed after the previous V2 run.

If only presentation/docs changed, do not waste cloud/model budget repeating unrelated Azure runs.

---

## Secret scan / evidence hygiene

Check that submission does not contain:

```text
Azure subscription secrets
OPERATIONS_ADMIN_KEY
access tokens
real .azure state
Terraform state
private evidence
connection strings
private local reports
```

The repository already ignores:

```text
.azure/
.venv/
.tools/
*.tfstate
*.tfplan
evidence/**/private/
```

Still manually inspect final staged changes.

---

## Cloud cleanup

After final evidence is safely captured:

```text
identify which resources must remain for judging
destroy / remove anything not required
```

Do not destroy a live endpoint if judges need it after submission.

If judging uses only video/repository evidence, clean up aggressively.

Record:

```text
resources retained
resources deleted
reason
expected cost exposure
```

Current read-only Azure inspection found no project resource group (only the
subscription's `NetworkWatcherRG`). The Terraform safe plan showed 17 possible
creates, but no `apply`, `azd provision`, or `azd deploy` should be run solely
to turn this checklist green without explicit budget authorization.

---

# 18. Phase 6 Verification Evidence Folder

Recommended **local** evidence layout:

```text
evidence/
└── phase6/
    ├── baseline/
    │   ├── tool-versions.txt
    │   └── git-baseline.txt
    ├── local/
    │   ├── unit-tests.txt
    │   ├── local-wiring.txt
    │   ├── history-audit.txt
    │   └── 15-scenarios.md
    ├── azure/
    │   ├── hosted-smoke.md
    │   ├── hosted-state.md
    │   ├── containment.md
    │   ├── approval-outcome.md
    │   └── telemetry.md
    ├── comparison/
    │   └── off-vs-on.md
    └── private/
        └── raw-sensitive-evidence/
```

Important:

```text
evidence/**/private/
```

is already ignored by repository policy.

Public evidence must be sanitized before commit.

The final submission may instead consolidate public results into:

```text
ReasonFuse_PHASE6_MICROSOFT_SUBMISSION_EVIDENCE.md
```

For the current cost-controlled repository, the consolidated public artifact is
the chosen layout. Do not create a large `evidence/` tree merely to satisfy this
example; retain sensitive/raw Azure material locally and untracked.

---

# 19. Standard Evidence Record

Use this template for every cloud signature run.

```markdown
## <RUN_ID> — <title>

- Timestamp:
- Commit SHA:
- Environment:
- Region:
- Hosted Agent:
- Release role:
- ReasonFuse enabled:
- Contract:
- Initial Operations state:
- User goal:
- Expected trajectory:
- Actual trajectory:
- Approval state:
- Detector / fuse reason:
- Pending postcondition:
- Final postcondition result:
- Final ReasonFuse state:
- Telemetry evidence:
- Result: PASS / FAIL / NOT VERIFIED / BLOCKED
- Evidence files/screenshots:
- Limitations:
```

Recommended run IDs:

```text
P6-LIVE-001  Hosted runtime
P6-LIVE-002  State continuity
P6-LIVE-003  Containment
P6-LIVE-004  Approval → Verified Outcome
P6-LIVE-005  Approval → Failed/Unknown Outcome
P6-LIVE-006  Telemetry
P6-LIVE-007  Toolbox/IQ optional
P6-LIVE-008  APIM optional
P6-COMP-001  OFF vs ON comparison
```

---

# 20. Failure Triage

When a Phase 6 cloud verification fails, classify before editing code.

## A — Environment / Quota

Examples:

```text
model quota unavailable
region capacity unavailable
subscription restriction
```

Action:

```text
fix environment
do not change ReasonFuse core
```

---

## B — Identity / Permission

Examples:

```text
RBAC propagation
Managed Identity permission
Toolbox/Search authorization
```

Action:

```text
fix identity boundary
do not change detector logic
```

---

## C — Deployment Wiring

Examples:

```text
wrong environment variable
Hosted code not updated
Operations endpoint missing
azd output not propagated
```

Action:

```text
fix deployment boundary
```

---

## D — Microsoft SDK/API Compatibility

Examples:

```text
preview API behavior changed
approval event schema changed
hosting beta package regression
```

Action:

```text
make the smallest compatibility fix
pin/document version
```

---

## E — Operations Demo Defect

Examples:

```text
fixture cannot reset
restart generation does not change
fresh/stale response cannot be distinguished
```

Action:

```text
fix the demo world
not the ReasonFuse algorithm
```

---

## F — ReasonFuse Core Correctness Defect

Examples:

```text
stale observation is incorrectly OUTCOME_VERIFIED
contained trajectory still dispatches
budget reservation allows unbounded verification
exact-loop classification wrong under the declared contract
```

Only category F justifies touching the frozen core.

Required response:

```text
minimal fix
→ V1
→ affected V2 scenarios
→ affected Azure signature run
→ claim audit
```

---

# 21. Verification Stop Conditions

Stop adding work and prepare submission when all P0 gates are green.

Do not continue because:

```text
"one more feature would look cool"
"we could make a dashboard"
"we could add another agent"
"we could run 100 more tests"
```

Phase 6 verification is complete when the evidence proves the thesis.

---

# 22. P0 Final Gate Checklist

## Local

```text
[ ] V0 baseline recorded
[ ] unit/boundary tests PASS
[ ] local_wiring PASS
[ ] local_history_audit PASS
[ ] compileall PASS
[ ] git diff --check PASS
[ ] 15 / 15 scenarios PASS
[ ] Terraform fmt PASS
[ ] Terraform validate PASS
[ ] safe plan PASS
```

The checklist remains an acceptance template. The current local results and
their evidence are recorded in the consolidated Phase 6 evidence document;
cloud checkboxes must not be checked from local fixture results.

## Azure / Microsoft

```text
[ ] Hosted Agent deployed
[ ] Responses 2.0.0 smoke PASS
[ ] Hosted session/state behavior proven
[ ] live deterministic containment proven
[ ] native approval generated before side effect
[ ] denial or no-pre-approval execution proven
[ ] approved restart executes
[ ] accepted result is not treated as success
[ ] fresh postcondition read occurs
[ ] OUTCOME_VERIFIED live path proven
[ ] failed/unknown outcome covered locally, preferably one live
[ ] Application Insights telemetry captured
```

## Comparative evidence

```text
[ ] ReasonFuse OFF controlled run
[ ] ReasonFuse ON controlled run
[ ] same initial conditions documented
[ ] tool-call metrics captured
[ ] redundant-call metrics captured where meaningful
[ ] verified-outcome difference captured
```

## Claims / submission

```text
[ ] architecture diagram matches current repo
[ ] six reliability capabilities match current implementation
[ ] Microsoft-native vs ReasonFuse-owned boundaries are explicit
[ ] README claims match evidence
[ ] 3-minute script claims match evidence
[ ] screenshots sanitized
[ ] secrets absent
[ ] final commit SHA recorded
```

---

# 23. P0.5 Checklist

Only if P0 is already complete:

```text
[ ] real Foundry Toolbox trace
[ ] real Foundry IQ trace
[ ] live APIM sticky-canary evidence
[ ] lightweight judge-facing capability status UI
[ ] second polished failure demo
```

Failure of P0.5 does not block submission.

---

# 24. Definition of Verified Phase 6

Phase 6 is **VERIFIED COMPLETE** only when we can truthfully say:

> A Microsoft Foundry Hosted Agent executed the ReasonFuse runtime path.  
> ReasonFuse deterministically detected and contained an unproductive trajectory.  
> A high-impact operation was gated by Microsoft native approval before execution.  
> The accepted side effect was not treated as success.  
> A fresh real-world observation was used to determine the postcondition outcome.  
> The important ReasonFuse decisions were visible in structured telemetry.  
> A small controlled OFF vs ON comparison demonstrated the value of the control layer.  
> The final repository and presentation make no claim stronger than the captured evidence.

---

# 25. Final Verification Principle

The final submission should not ask the judge to trust architecture slides.

It should let the judge see:

```text
Agent proposes
        ↓
ReasonFuse observes
        ↓
ReasonFuse decides
        ↓
Microsoft approval gates risk
        ↓
Tool changes the world
        ↓
ReasonFuse verifies the world
        ↓
Evidence proves the result
```

The Phase 6 verification standard is therefore:

> **Do not prove that ReasonFuse has many features. Prove that its most important control guarantees actually happen in the Microsoft runtime.**
