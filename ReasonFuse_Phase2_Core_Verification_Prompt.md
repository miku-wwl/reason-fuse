# ReasonFuse Phase 2 — Core Verification Prompt

> **Purpose:** Independently verify that the Phase 2 ReasonFuse P0 core actually works on the validated Microsoft runtime.  
> **Audience:** Next independent validation agent  
> **Phase:** 2 — ReasonFuse Core  
> **Role:** Validator, not implementer  
> **Prerequisite:** Phase 1 independent PASS + Phase 2 construction complete with audited evidence  
> **Primary Exit Gate:** `OFF/ON + Outcome Verification PASS`

---

# 0. Current Repository Handoff (2026-09-09 NZ / evidence 2026-09-08 UTC)

Work in `D:\workshop\sep\reason-fuse`. This is the root file
`ReasonFuse_Phase2_Core_Verification_Prompt.md`, not a nested `_Phase2` project.
Continue the existing application; do not alter the historical Construction Prompt.

Read these three materials before executing:

| Material | Purpose |
| --- | --- |
| [Construction report](docs/phases/phase-02-core/report.md) | Completed fixes, actual tests and dated deployment |
| [Open questions](docs/phases/phase-02-core/open-questions.md) | Remaining evidence boundaries; not implicit PASS |
| [Construction evidence index](evidence/phase-02-core/index.json) | Paths, hashes, commands and all attempts in the final batch |

Use the [Core runbook](docs/phases/phase-02-core/runbook.md) and the retained
[Phase 1 independent report](docs/phases/phase-01-runtime-validation/verification-report.md).
The construction handoff has 36 unit tests, LOCAL_CORE/LOCAL_INTEGRATION, final
Hosted A–J, compatibility regression and scoped reset PASS. This does not award
independent Phase 2 PASS. Superseded learning intermediates were removed at the
owner's request; do not recover or review them. Use the current report/index.

Construction delivery was pushed to GitHub main at `dcb7b8322979daf46505c3e7718108842cb96bc6` before
this Verification Prompt was adjusted. Runtime source commit is
`4fb12e6c34f77b3a0814f55fc268e10487111ad7`, source manifest
`8b8c1247360c93469bfc982920136d2adc0ec8dd800ea1bb286927712773b11e`, audited native ZIP
`8e9f9f9ade984691c21e73584e01a16f6988e2d3d7a59cc23db10ee3c132ac8b`.
The final captured deployment is stable 27 / candidate 13, both active, Toolbox 11,
profile `phase2`, enabled `true`, contract JSON `{}`. These are dated snapshots:
read back current source, package, actual configuration and releases before testing.
Fresh audited redeployment can legitimately change embedded git revision/package
hash; compare with that deployment's new audit, not a permanently hardcoded hash.
Documentation commits do not themselves redeploy the runtime.

Keep the frozen Microsoft path, existing Australia East resources and Terraform
ownership. Retain `.azure/` state, Python 3.13 and locked dependencies/tools. No
resource-group teardown, new cloud architecture, custom history/approval database,
custom RAG or alternate MCP transport. Critical tools still cross local Function
Middleware and managed Foundry Toolbox. Client Responses uses `store=True`, the
downstream model uses `store=False`; native approval remains
`mcp_approval_request` / `mcp_approval_response`.

## Executable entry points and configuration matrix

Run from the repository root. Record a new `verification-<UTC>` batch and a fixed
trial plan BEFORE the first trial. Run shared-counter scenarios sequentially.

```powershell
pwsh -File scripts/bootstrap.ps1
uv sync --frozen --python 3.13
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m unittest discover -s tests/unit -v
.venv/Scripts/python.exe scripts/phase2_local.py
.venv/Scripts/python.exe scripts/phase2_operations_local.py
pwsh -File scripts/preflight.ps1
.venv/Scripts/python.exe scripts/capture_environment.py
```

| Driver case | Required deployed configuration | Primary proof |
| --- | --- | --- |
| `a-off` | profile phase2, enabled false, contract `{}` | Four-turn harness baseline |
| `b-on` | enabled true, contract `{}` | Same prompts/default contract; NO_PROGRESS |
| `c-exact`, `d-oscillation`, `h-budget` | enabled true; only max_stalled_steps=20 and required_objective_progress_interval=20 override defaults | Isolated detector/budget boundary |
| `e-retrieval`, `f-useful`, `g-outcome-failure`, `i-outcome-unknown`, `j-database-recheck` | enabled true, contract `{}` | Churn, both useful-check tools, three outcomes |

Every row uses `REASONFUSE_PROFILE=phase2`; the resource names remain unchanged.

The actual driver is `scripts/phase2_hosted.py <case> --batch verification-<UTC>`.
Use `--turn-delay 45` for H: one explicitly requested DNS per turn, 10 executions,
11th proposal blocked. Fixed pacing reduces quota pressure; it does not relax
budgets. Do not run `all` under a single configuration: A and C/D/H need different
deployments. Set trusted config with the project-local
`.tools/azd-1.33.0/azd-windows-amd64.exe env set`; use `scripts/deploy.ps1` for full
audited deployment, and the pinned azd `deploy stable --no-prompt` only for
same-package configuration switches. Compare OFF/ON at the explicit stable endpoint.
Always restore enabled true and contract `{}` in finally, deploy and read back.

`scripts/phase2_construction.ps1` and `scripts/phase2_index.py` are construction
reproduction/indexing helpers, NOT independent acceptance or the repeat campaign.
Use `scripts/verification_command.py <label> -- <command>` to retain command output;
link its shared recorder files into the new independent evidence index. The local
drivers also write to `local-<UTC-date>`; index their exact paths/hashes as LOCAL,
not Hosted. Do not select PASS from unrelated batches or omit failed attempts.

After core tests, run `scripts/verification_batch.py verification-<UTC>-compatibility`
as a separate compatibility gate, not a Phase 2 detector test. This retains the
14-command preflight/identity/history/interception/approval/APIM/SSE/metadata suite
and its fixed 60-client routing control. Finally run `scripts/reset.py` and retain
its zero-counter, baseline-world and recorded-session deletion readback.

---

# 1. Mission

Validate the real ReasonFuse core.

Your job is not to make the implementation look successful.

Your job is to falsify incorrect detector logic, unsafe containment, false positives, and fake outcome verification.

Phase 2 passes only when the core behaves correctly in real execution.

Return:

```text
Core OFF/ON             PASS / FAIL
Exact Loop              PASS / FAIL
Oscillation             PASS / FAIL
Retrieval Churn         PASS / FAIL
Useful Recheck          PASS / FAIL
Run Contract            PASS / FAIL
Outcome Verification    PASS / FAIL
State / Middleware      PASS / FAIL
Outcome Unknown         PASS / FAIL
Compatibility / Reset   PASS / FAIL

PHASE 2 RESULT:
PASS / BLOCKED
```

---

# 2. Validation Rules

## Rule 1 — Do Not Accept Unit Tests Alone

Unit tests are supporting evidence.

Phase 2 requires:

```text
live/integration execution
```

on the validated runtime path.

---

## Rule 2 — Same Inputs for OFF / ON Comparison

The OFF/ON comparison must preserve:

```text
same model
same prompt
same tools
same world state
same scenario
same dependency versions
```

The only intended behavioral variable is:

```text
ReasonFuse enforcement OFF / ON
```

Keep source/package, selected backend, contract limits, model and tool schemas
constant. Reset produces a NEW epoch for each trial: compare equivalent starting
world states across OFF/ON, and require unchanged epoch only WITHIN a trial.
Use the same first four driver prompts. Distinguish HARNESS_STOP, voluntary model
stop and fuse stop; model refusal or voluntary stopping is not containment proof.

---

## Rule 3 — False Positives Are Critical Failures

A detector that blocks legitimate verification is not acceptable.

Useful Recheck preservation must be explicitly tested.

---

## Rule 4 — Model Self-Reporting Is Not Proof

Do not accept:

```text
"I made progress"
"Todo completed"
"I think the service recovered"
```

as objective progress or outcome success.

Use structured tool/world-state evidence.

---

# 3. Environment Audit

Record:

```text
date/time
Foundry project
region
agent version
toolbox version
knowledge/retrieval version if applicable
model version

agent-framework version
foundry-hosting version
azure-ai-projects version

ReasonFuse contract version
git commit
```

Run Phase 2 preflight/reset.

Audit embedded build identity, actual stable/candidate content hashes, native ZIP
manifest, Toolbox schema and actual env values. Do not infer deployed code from
local HEAD alone. Keep body/message-content capture disabled and keys/cookies out
of evidence. Retain only bounded synthetic payloads and nonsecret metadata.

Confirm Phase 1 critical runtime path still works.

If Phase 1 assumptions regressed:

```text
STOP
classify failure
```

---

# 4. State Model Validation

Inspect the live `AgentSession` / structured state.

Confirm ReasonFuse keeps:

```text
trajectory_state
progress_state
recent fingerprints
evidence state
retrieval state
world-state state
stall counter
oscillation window
Run Contract counters
postcondition state
```

Confirm the state is not reconstructed from prompt text.

Required:

```text
ReasonFuse state survives multiple tool calls in one run
```

Also prove changed counters, pending postcondition, useful-recheck allowance and
mode/contract survive multiple turns and native approval pause/resume. A new
conversation starts a new run; resume must not reset budgets or create a new run_id.
Use core namespace `reasonfuse_core_v1`, not the Phase 1 validation marker namespace
`reasonfuse`. Distinguish `framework_session_id` (AgentSession) from platform
`agent_session_id`. If the SDK leaves core conversation_id unset, record the real
conversation ID from the Responses client alongside both IDs; do not invent one.
Test malformed state and changed contract restoration fail closed.

---

# 5. OFF Mode Validation

Set:

```text
REASONFUSE_ENABLED=false
```

Run the deterministic no-progress scenario.

Expected:

```text
repeated investigation continues
ReasonFuse does not block
```

Capture:

```text
tool sequence
tool call count
run duration
reasonfuse_enabled=false
```

OFF mode may emit telemetry but must not enforce containment.

Locally exceed each budget in OFF and prove no ReasonFuse block. Native approval,
RBAC and safety controls remain active. The live OFF harness has a fixed ceiling;
do not run an unbounded experiment or mistake the ceiling for fuse enforcement.

PASS only if the baseline can visibly continue into redundant behavior.

---

# 6. ON Mode Validation

Reset the environment to the exact same starting state.

Set:

```text
REASONFUSE_ENABLED=true
```

Use the same:

```text
prompt
model
tools
scenario
world state
```

Expected:

```text
objective progress remains zero
stall threshold reached
Behavioral Fuse trips
execution contained
```

Capture:

```text
step where containment occurred
fuse reason
objective-progress signals
tool calls avoided after containment
```

Required result:

```text
OFF
→ continues redundant execution

ON
→ contains redundant execution
```

---

# 7. Objective Progress Validation

Validate each signal independently.

## Evidence Delta

Create:

```text
same diagnostic result twice
```

Expected second call:

```text
Evidence Delta = 0
```

Then introduce genuinely new diagnostic evidence.

Accumulate evidence across tool types/resources: switching away and back must not
make old evidence new. Request IDs, counters, timestamp noise and missing unrelated
observations must not manufacture objective progress.

Expected:

```text
Evidence Delta > 0 / true
```

---

## World-State Delta

Before external state change:

```text
World-State Delta = 0
```

After deterministic restart/state transition:

```text
World-State Delta = positive
```

Only an independently observed relevant transition counts. HTTP 202/accepted alone
is NOT world progress. Compare snapshots per resource; missing world observation
is not disappearance or change. A rejected action creates no successful outcome.

---

## Retrieval Delta

Equivalent retrieved evidence with different query wording:

```text
Retrieval Delta = 0
```

New source/evidence:

```text
Retrieval Delta = positive
```

Test source/citation/chunk/content-hash normalization and knowledge-base version.
Equivalent query wording/scores do not count; a real new source/version interrupts
churn. Missing retrieval fields on a non-retrieval call do not change its evidence.
Hosted E uses a deterministic Toolbox fixture: label it explicitly and keep
`Foundry IQ integration: NOT VERIFIED`. Do not substitute fixture proof for IQ.

---

## Todo Delta

Change:

```text
OPEN → COMPLETED
```

while objective evidence remains unchanged.

Required:

```text
Todo Delta = positive

BUT

Objective Progress = false
```

This is mandatory.

Read the actual TodoProvider state. Test OPEN/IN_PROGRESS/COMPLETED across persisted
turns without resetting stall counters solely because the plan changed.

---

## Postcondition Delta

Create a successful external state transition.

Required:

```text
Postcondition Delta = positive
```

---

# 8. Exact Loop Validation

For C, raise BOTH stall and required-objective-progress interval to 20 before
deployment. Keep the remaining default budgets. Otherwise default NO_PROGRESS
may legitimately precede the detector being tested. Capture completed calls and
blocked proposals separately: two executions, third proposal blocked.

Run:

```text
dns_resolution("api.reasonfuse.local")
dns_resolution("api.reasonfuse.local")
dns_resolution("api.reasonfuse.local")
```

with no objective progress.

Confirm canonical fingerprints are identical.

Expected:

```text
EXACT_LOOP
→ FUSE_TRIPPED / BLOCK
```

Also test equivalent argument dictionary ordering if relevant.

Fingerprint must remain stable.

---

# 9. Oscillation Validation

Run a deterministic pattern:

```text
dns_resolution("api.reasonfuse.local")
dns_resolution("payments.reasonfuse.local")
dns_resolution("api.reasonfuse.local")
dns_resolution("payments.reasonfuse.local")
```

with no objective progress.

Expected:

```text
OSCILLATING
→ BLOCK
```

This is the current Hosted D fixture. Three calls execute; the fourth proposal is
blocked. Also test the original service_status/database_health pattern locally,
with stable per-resource observations, and prove genuine new evidence interrupts
oscillation. Use the same isolated C/D/H contract from Section 0.

Negative control:

Introduce real new evidence between the same actions.

Expected:

```text
no false oscillation trip
```

---

# 10. Retrieval Churn Validation

Run semantically different retrieval queries that return equivalent effective evidence.

Example:

```text
"database failure"
"db connectivity"
"database issue"
```

all resolve to the same normalized evidence set.

Expected:

```text
Retrieval Churn counter increases
threshold reached
RETRIEVAL_CHURN
→ BLOCK
```

Negative control:

Return one genuinely new source.

Expected:

```text
retrieval progress resets/advances appropriately
no premature churn block
```

---

# 11. Useful Recheck Validation

This is a critical anti-false-positive test.

## Useful Case

Run:

```text
database_health()
↓
restart_service()
↓
database_health()
```

where restart changes the relevant world state.

Required:

```text
second database_health
= useful recheck
= ALLOW
```

ReasonFuse must not block it as a duplicate.

Test BOTH service_status (F) and database_health (J); they share the fixture health
schema. Assert useful_recheck from actual persisted runtime state, not a driver
constant or model text. A newly accepted action creates exactly one bound
verification obligation even if the service remains UNHEALTHY. Bind it to the
action/resource/generation; unrelated reads neither inherit nor consume it.
The first failed/stale bound read consumes that allowance and returns a failure
or unknown outcome; it must not grant unlimited retries. Test across serialized
AgentSession restoration and native approval resume. A denied action creates no
postcondition obligation or external dispatch.

---

## Wasteful Case

Run:

```text
database_health()
↓
database_health()
↓
database_health()
```

with no state change.

Required:

```text
wasteful repetition
→ eventually contained
```

---

# 12. Run Contract Validation

Test each critical contract dimension at least once.

At minimum:

```text
max_steps
max_tool_calls
max_stalled_steps
max_side_effects
required_objective_progress_interval
```

Frozen defaults: steps=12, tools=10, stalled=2, side effects=1,
objective-progress interval=2, oscillation cycles=2, retrieval churn=3,
require_postcondition_for_side_effects=true. Validate invalid bool-as-int limits
and out-of-window detector thresholds are rejected. Capture trusted config and
prove it remains fixed through resume; prompt text cannot increase it.

Before a side effect, reserve its required verification INSIDE both step/tool
limits: at least two slots must remain for action plus one read. A pending read
keeps its reserved slot. Count attempted failed dispatches; blocked proposals and
native denials are not executed tools. read_runtime_state is observation-only.
Side-effect budget exhaustion must not block legitimate read-only diagnostics.
H must show exactly budget-1..budget-10 DNS executions and no extra external tools,
then block proposal 11. Test step and progress-interval boundaries separately in
LOCAL_CORE; do not claim those local tests are additional Hosted budget scenarios.
Non-default multi-action/concurrent operation is not covered by P0's limit of one;
record any pending-postcondition overwrite concern before broadening that scope.

Expected when exceeded:

```text
BUDGET_EXHAUSTED
or
appropriate deterministic fuse reason
```

Do not allow the model to exceed the configured contract silently.

---

# 13. Outcome Verification — Failure Path

Reset the world.

Configure:

```text
restart_service("orders")
→ execution accepted / HTTP 202
→ service remains UNHEALTHY
```

Required:

```text
Tool execution status = accepted
Outcome status = POSTCONDITION_FAILED
```

The system must NOT report success merely because the tool returned 2xx/accepted.

Capture the verification tool call and final world state.

---

# 14. Outcome Verification — Success Path

Reset.

Configure:

```text
restart_service("orders")
→ accepted
→ service becomes HEALTHY
```

Required:

```text
OUTCOME_VERIFIED
```

Verify the postcondition using a real deterministic check, not an LLM statement.

---

# 15. Unknown Outcome Path

This is MANDATORY in the implemented Phase 2 contract. Validate:

```text
verification unavailable or inconclusive
→ OUTCOME_UNKNOWN
```

Hosted I must reject stale HEALTHY as OUTCOME_UNKNOWN. Before declaring HEALTHY
success, verify exact resource, fresh post-acceptance generation, valid health and
observation status. Locally cover timeout, unavailable, malformed/missing health,
mismatched resource and stale generation; label each evidence layer accurately.
After unknown/failure, prove subsequent external dispatch is contained. Missing
or malformed data must never be silently promoted to OUTCOME_VERIFIED. Do not
defer this gate or treat accepted/HTTP 202 as outcome success.

---

# 16. Middleware Enforcement Validation

Confirm ReasonFuse-critical calls still flow through:

```text
Function Calling Middleware
```

For at least one contained scenario, prove:

```text
PRE-call decision
→ BLOCK
→ external tool execution count does not increase
```

This ensures Phase 2 did not accidentally move critical tools to a provider-hosted bypass path.

Also prove a fuse tripped AFTER a completed call blocks subsequent calls without
mislabeling the completed call as prevented. Use independent Operations counters,
same-epoch before/after snapshots and authoritative read_runtime_state. Native
approval tests must still cover approve once, deny, consumed-ID replay and argument
binding; prose approval is not authorization.

---

# 17. Determinism Validation

Repeat core detector scenarios multiple times after reset.

At minimum:

```text
Exact Loop × 3
Oscillation × 3
Retrieval Churn × 3
Useful Recheck × 3
Outcome Failure × 3
```

Expected classification should be stable.

Record any nondeterminism.

Do not tune acceptance criteria after seeing results.

Use fresh conversations and reset world state BETWEEN trials; never reset shared
counters within a proof interval. Run F and J at least once each, and repeat the
chosen useful-recheck path three times. Keep every attempt, including quota/setup
failures, with classification and corrective action; do not silently retry or
select an earlier PASS. Record the fixed pacing/trial policy up front. Construction
results are the starting evidence, not any of these new independent repetitions.

---

# 18. Negative Controls

Phase 2 must include negative controls.

Required examples:

```text
repeated tool call after world-state change
→ should NOT be classified as waste

same two actions with new evidence
→ should NOT be oscillation failure

retrieval query with new source
→ should NOT be churn

Todo completed without evidence
→ should NOT count as objective progress
```

PASS requires both:

```text
fault detection
AND
healthy preservation
```

---

# 19. Telemetry Validation

Inspect emitted OTel/tracing data.

Confirm key attributes exist where applicable:

```text
trajectory_state
progress_state
evidence_delta
world_state_delta
retrieval_delta
todo_delta
postcondition_delta
useful_recheck
failure_type
fuse_reason
contract_version
```

Do not fail Phase 2 solely for cosmetic trace presentation issues, but missing core decision evidence is a failure.

Inspect `reasonfuse.*` attributes/events, not just generic APIM access logs. Local
span emission tests and Hosted runtime state are separate from cloud collector
correlation. Query a new B/F/G/I request/run and preserve the correlated decision
trace where available; report an instrumentation/export/query gap explicitly.
Never claim APIM metadata PASS proves Core span export. Keep body/message capture
disabled. No production transcripts, tokens, admin keys, connection strings or
cookie values in telemetry or committed evidence; synthetic test payloads must
remain bounded and nonsecret, as in Section 0.

---

# 20. Clean-Start Revalidation

After all scenarios pass:

```text
reset environment
restart services as required
deploy/run from documented commands
run preflight
run OFF/ON
run Useful Recheck
run Outcome Failure
run Outcome Unknown
```

OFF/ON, Useful Recheck, Outcome Failure and Outcome Unknown must pass from a clean
start. Use a fresh locked full `scripts/deploy.ps1` audit, preserve current Azure
state, then apply the configuration matrix as needed. A process-only restart or
reusing the construction ZIP's old PASS label is insufficient. No resource teardown
is required. Restore default ON after testing and record final reset readback.

---

# 21. Failure Classification

Classify every issue as:

```text
IMPLEMENTATION_BUG
TEST_DATA_BUG
SCENARIO_RESET_BUG
CONFIGURATION_ERROR
SDK_INTEGRATION_ERROR
DETECTOR_LOGIC_ERROR
ARCHITECTURE_ASSUMPTION_FAILURE
EXTERNAL_SERVICE_OR_QUOTA_FAILURE
```

Architecture should only be reopened for `ARCHITECTURE_ASSUMPTION_FAILURE`, not
for quota limits or other transient external failures.

Do not redesign because a detector implementation is wrong.

Validate first. If the execution request authorizes fixes, make only scoped
project-owned corrections, preserve the original failure and rerun affected gates
on the new audited source. A source change invalidates the prior candidate's final
acceptance; record the retest boundary explicitly. Otherwise document the exact
reproducer and request authority. Do not lower gates to turn a failure into PASS.

---

# 22. Required Phase 2 Evidence

For every required scenario capture:

```text
scenario ID/name
OFF / ON
run_id
conversation_id
agent_session_id
framework_session_id

source manifest / audited ZIP / deployed configuration
scenario epoch and before/after world snapshots
HARNESS_STOP / voluntary_stop / fuse stop
tool sequence
tool execution counters
fingerprints where relevant

Evidence Delta
World-State Delta
Retrieval Delta
Todo Delta
Postcondition Delta

trajectory state
fuse reason
containment step

postcondition result

trace/request ID if available
```

Save evidence under:

```text
evidence/phase-02-core/verification-<UTC>/
```

Create an index in that directory with command, UTC timestamp, exit status,
evidence layer, exact repo-relative path and SHA-256 for each required gate and
attempt, source manifests, audited ZIP and final reset. Shared recorder/local
artifacts may remain in their existing directories but must be explicitly indexed.
Do not overwrite `evidence/phase-02-core/index.json`, which is the construction
handoff, or rewrite construction evidence to contain independent PASS labels.

---

# 23. Phase 2 Report

Create separate independent reports (do not overwrite the construction report):

```text
docs/phases/phase-02-core/verification-report.md
docs/phases/phase-02-core/verification-open-questions.md
```

The main report must be self-contained: process, environment/source identity,
trial plan, fixes and retests, evidence links, each gate's actual result, final
reset, and an explicit decision. Put unresolved issues/doubts and exact next steps
in the second Markdown. Separate LOCAL, REAL_HOSTED and NOT VERIFIED findings.

Required format:

```text
# Phase 2 ReasonFuse Core Validation Report

## Environment
...

## OFF Baseline
PASS / FAIL
Evidence:
...

## ON No-Progress
PASS / FAIL
Evidence:
...

## Exact Loop
PASS / FAIL

## Oscillation
PASS / FAIL

## Retrieval Churn
PASS / FAIL

## Useful Recheck
PASS / FAIL

## Run Contract
PASS / FAIL

## Outcome Failure
PASS / FAIL

## Outcome Success
PASS / FAIL

## Outcome Unknown
PASS / FAIL

## Todo-Only Progress Negative Control
PASS / FAIL

## Middleware Enforcement
PASS / FAIL

## Determinism Repeats
PASS / FAIL

## Clean-Start Revalidation
PASS / FAIL

## Compatibility Regression Gate (Phase 1)
PASS / FAIL

## Final Default-ON Restore and Scoped Reset
PASS / FAIL

## Evidence Boundaries
Foundry IQ / production restart / concurrency / cloud Core trace correlation

## Architecture Change Required?
YES / NO

## Phase 2 Result
PASS / BLOCKED
```

---

# 24. Phase 2 PASS Gate

Return:

```text
PHASE 2 RESULT: PASS
```

only if all are true:

```text
[ ] OFF baseline visibly continues redundant behavior

[ ] ON mode contains the same no-progress behavior

[ ] Exact Loop PASS

[ ] Oscillation PASS

[ ] Retrieval Churn PASS

[ ] Useful Recheck preservation PASS

[ ] Todo-only change does not count as objective progress

[ ] Run Contract enforcement PASS

[ ] Outcome failure correctly returns POSTCONDITION_FAILED

[ ] Outcome success correctly returns OUTCOME_VERIFIED

[ ] stale/missing/inconclusive verification cannot claim success; OUTCOME_UNKNOWN PASS

[ ] critical tool blocking prevents real execution

[ ] detector results are stable across repeated resets

[ ] clean-start OFF/ON + Useful Recheck + Outcome Failure + Outcome Unknown PASS

[ ] current deployed source/configuration and audited ZIP identity verified

[ ] native history/approval/interception/APIM compatibility gate PASS

[ ] final default ON restored; recorded test sessions deleted/absent, counters zero, world baseline

[ ] separate reports and complete hashed evidence index retained, including all attempts

[ ] no frozen architecture assumption failed
```

---

# 25. BLOCKED Gate

Return:

```text
PHASE 2 RESULT: BLOCKED
```

if any critical core capability cannot be validated after reasonable diagnostic work.

Do not downgrade required tests into optional tests to obtain PASS.

---

# 26. Final Validator Instruction

Phase 2 is not a coding-completion review.

It is a behavioral reliability review.

The key question is:

> **Does ReasonFuse correctly contain no-progress behavior while preserving legitimate investigation and verifying real-world outcomes?**

The desired result is:

```text
ReasonFuse OFF
→ agent keeps wasting work

ReasonFuse ON
→ agent is contained

Useful verification
→ preserved

Accepted side effect with failed real-world result
→ POSTCONDITION_FAILED
```

If those behaviors are not proven by real execution, Phase 2 is not complete.

The acceptance is explicitly bounded to the simulated Operations API and
deterministic retrieval fixture. Do not claim production service recovery, real
Foundry IQ integration, arbitrary concurrent/forked turns or forced cold-start
recovery without separate evidence. Do not add later-phase benchmarks/dashboards.
Retain Azure resources for the next phase. This prompt alone does not authorize
commit/push, infrastructure teardown, architecture expansion or historical-file
recovery; follow the current user's explicit delivery authorization separately.
