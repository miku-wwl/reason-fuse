# ReasonFuse Phase 2 — Core Construction Prompt

> **Purpose:** Implement the first real working ReasonFuse P0 core on top of the validated Phase 1 runtime.  
> **Audience:** Luna / next construction agent  
> **Phase:** 2 — ReasonFuse Core  
> **Expected effort:** 10–14 hours  
> **Prerequisite:** Independent Phase 1 **4/4 PASS + clean-start PASS + deployed-source identity verified**  
> **Architecture status:** FROZEN — ReasonFuse v4.1.3 / v4.1.2 freeze lineage  
> **Primary Exit Gate:** `ReasonFuse OFF/ON + Outcome Verification PASS`

---

# 0. Current Repository Handoff (2026-09-08)

Work in the existing repository root: `D:\workshop\sep\reason-fuse`.
The actual filename is `ReasonFuse_Phase2_Core_Construction_Prompt.md`; do not
create a nested `ReasonFuse/_Phase2/` application or a second Python project.

Read these before taking construction actions:

| Source | Authority |
| --- | --- |
| [README](README.md) | Current single-project layout |
| [Independent Phase 1 report](docs/phases/phase-01-runtime-validation/verification-report.md) | Current acceptance decision; construction-time PASS is insufficient |
| [Validation boundaries](docs/phases/phase-01-runtime-validation/verification-open-questions.md) | No open Phase 1 blockers; capabilities not yet verified |
| [Phase 1 verification rubric](ReasonFuse_Phase1_Runtime_Validation_Verification_Prompt.md) | Frozen runtime acceptance scope |
| [Runbook](docs/phases/phase-01-runtime-validation/runbook.md) | Azure ownership, deployment, testing and reset |
| `azure.yaml`, `src/reasonfuse/agent.py`, `src/reasonfuse/validation/` | Actual runtime composition and validation hooks |
| `pyproject.toml`, `uv.lock`, `requirements.txt`, `scripts/bootstrap.ps1`, `infra/.terraform.lock.hcl` | Pinned dependency/tool baseline |

Use the final report and its linked acceptance evidence as the Phase 1 baseline.
Superseded reports and diagnostic attempts were removed in the owner's learning
cleanup. Do not recover, review or investigate those historical attempts for
Phase 2. This prompt does not itself confer a Phase 1 PASS.

At this 2026-09-08 handoff, the independent report records all four spikes and
the full clean-start as PASS in both corrected batches. Active releases are
stable 8 / candidate 5, Toolbox 6, with both Hosted content hashes equal to the
audited ZIP SHA-256 `d7b0ddeb3e2aa21a24360dbcfced1a017d35806e07d171f796a7d9e2e011eb97`.
The dated handoff is summarized in the Phase 1 reports; its temporary execution
artifacts are not part of the retained repository deliverable.
This is a dated handoff, not permission to ignore subsequent source/deployment drift.

If the current report is BLOCKED, stop Phase 2 construction and report the exact
missing gate. Do not reinterpret a prompt revision as permission to skip it.

Existing cloud resources remain in Australia East, subscription
`7c73b89d-485e-43a9-8d66-b12b766d567f`, resource group
`rg-reasonfuse-phase1-aue`, Foundry project `reasonfuse-phase1`.
Retain their names and Terraform ownership. Never delete `.azure/` or provision
existing resources from empty state. No resource-group teardown is required.

Use PowerShell 7 and the project-local pinned azd executable. Preserve Python
3.13, core 1.17.0, foundry 1.12.0, hosting 1.0.0b260903, projects 2.3.0,
identity 1.25.3 and agentserver-responses 2.2.0b1 unless a separately evidenced
compatibility blocker requires an explicitly reviewed change. Do not install the
all-integrations Agent Framework umbrella or Full Harness.

Current Phase 1 scope is deliberately bounded: DNS returns controlled results;
restart is `SIMULATED_RESTART`; release/SSE probes use deterministic middleware.
It does not prove production service recovery, model token streaming, concurrent
turn correctness, forced cold-start recovery, or Foundry IQ retrieval. Phase 2
must not inherit those as already-validated capabilities.

---

# 1. Mission

Phase 2 is the first phase in which you implement the actual ReasonFuse product logic.

After the hard prerequisite below is satisfied, extend the validated, bounded
Microsoft runtime. Do not assume that untested Phase 2 capabilities were proved
by Phase 1.

Your job is to build the smallest production-shaped ReasonFuse core that can demonstrate:

```text
1. Runtime objective-progress tracking
2. Exact-loop detection
3. Oscillation detection
4. Retrieval-churn detection
5. Useful-recheck preservation
6. Run Contract enforcement
7. Outcome Verification
8. Deterministic containment
9. ReasonFuse OFF / ON behavioral contrast
```

The Phase 2 result must be a working P0 core, not a prototype that only passes mocked unit tests.

---

# 2. Hard Prerequisite

Before changing code, inspect the Phase 1 report.

Required:

```text
Spike 1 — PASS
Spike 2 — PASS
Spike 3 — PASS
Spike 4 — PASS

Architecture Unfreeze Required?
NO

Clean-start revalidation — PASS
Deployed-source/dependency identity — VERIFIED
PHASE 1 RESULT — PASS
```

If Phase 1 is not fully PASS:

```text
STOP
```

Do not continue Phase 2 against an unvalidated runtime.

---

# 3. Frozen Runtime Boundary

Do not redesign this:

```text
Foundry Hosted Agent
 ↓
Responses 2.0.0
 ↓
ResponsesHostServer(
    history_source="agent_server"
)
 ↓
Agent Framework Agent
 ├─ TodoProvider
 ├─ AgentModeProvider
 ├─ AgentSession
 ├─ Tool Approval
 └─ ReasonFuse Middleware
      ├─ Agent Run Middleware
      └─ Function Calling Middleware
            ↓
      Local Tool / MCP Invocation
            ↓
      Foundry Toolbox
      ├─ Foundry IQ / retrieval path (not implemented or validated by Phase 1)
      └─ Operations OpenAPI
            ↓
      Outcome Verifier
```

Phase 2 must extend this exact runtime.

`src/main.py` remains the Hosted entry point; `src/reasonfuse/main.py` owns the
host and `src/reasonfuse/agent.py` composes the agent. Canonical client calls use
`store=True`; the downstream model client uses `store=False`. Do not conflate
these settings. The hosting SDK's transient history buffer is not an additional
canonical history owner; keep runtime evidence that its state is cleared between
turns and no transcript is replayed twice.

Keep native `mcp_approval_request` / `mcp_approval_response`. Submitting a high-impact
tool call asks the runtime to pause for approval; it is not executing the action.
Never ask the model to acquire prose approval before it submits the call. Preserve
the explicit Phase 1 instructions explaining this distinction. User prose,
consumed approval IDs and approval for different arguments are not authorization.

---

# 4. Non-Negotiable Rules

## Rule 1 — No Architecture Expansion

Do not add:

```text
Redis
Cosmos DB
Postgres
AKS
Kubernetes
Service Bus
Event Hub
Durable Functions
custom conversation store
custom approval database
custom RAG platform
custom MCP transport
multi-agent orchestration
custom evaluation platform
```

Phase 2 is a core-behavior phase.

---

## Rule 2 — Deterministic Runtime Decisions

Runtime containment must not depend on:

```text
LLM judge
free-form model confidence
arbitrary model self-assessment
natural-language "progress score"
```

ReasonFuse runtime decisions must be based on structured state and deterministic rules.

---

## Rule 3 — Todo Is Planning, Not Objective Progress

`Todo Delta` may be captured, but:

```text
Todo Delta alone
MUST NOT
reset the no-progress timer
```

Objective progress is:

```text
Evidence Delta
World-State Delta
Retrieval Delta
Postcondition Delta
```

---

## Rule 4 — Preserve Useful Rechecks

Repeated calls are not automatically bad.

ReasonFuse must allow legitimate verification after meaningful state change.

This is a required correctness property, not an optional enhancement.

---

# 5. Phase 2 Deliverables

Implement the following P0 modules:

```text
ReasonFuse State
Trajectory Model
Progress Engine

Evidence Delta
World-State Delta
Retrieval Delta
Todo Delta as planning signal
Postcondition Delta

Exact Loop Detector
Oscillation Detector
Retrieval Churn Detector
Useful Recheck Classifier

Run Contract
Behavioral Fuse
Containment Result

Postcondition Registry
Outcome Verifier

ReasonFuse OFF mode
ReasonFuse ON mode

Core integration tests
Core live scenarios
Phase 2 evidence
docs/phases/phase-02-core/report.md
docs/phases/phase-02-core/open-questions.md
evidence/phase-02-core/<batch>/index.json
```

---

# 6. Recommended Repository Structure

Use or adapt the existing repository.

Recommended:

```text
src/reasonfuse/
├── agent.py
├── main.py
├── validation/                  # retain Phase 1 regression probes
├── state/
│   └── reasonfuse_state.py
│
├── middleware/
│   ├── run_middleware.py
│   └── function_middleware.py
│
├── behavioral/
│   ├── trajectory.py
│   ├── progress_engine.py
│   ├── evidence_delta.py
│   ├── world_state_delta.py
│   ├── retrieval_delta.py
│   ├── todo_delta.py
│   ├── useful_recheck.py
│   ├── exact_loop.py
│   ├── oscillation.py
│   ├── retrieval_churn.py
│   ├── run_contract.py
│   └── behavioral_fuse.py
│
├── verification/
│   ├── registry.py
│   └── outcome_verifier.py
│
└── telemetry/
    └── tracing.py
```

Tests:

```text
tests/
├── unit/
│   ├── test_exact_loop.py
│   ├── test_oscillation.py
│   ├── test_retrieval_churn.py
│   ├── test_useful_recheck.py
│   ├── test_run_contract.py
│   └── test_outcome_verifier.py
│
└── integration/
    ├── test_off_on_no_progress.py
    ├── test_useful_recheck_live.py
    ├── test_outcome_failure_live.py
    └── test_budget_exhaustion_live.py
```

---

# 7. ReasonFuse State Model

Implement a typed structured state.

At minimum:

```text
run_id
conversation_id
agent_session_id

trajectory_state
progress_state

step_index
tool_call_count
side_effect_count

recent_actions[]
recent_action_fingerprints[]

evidence_keys[]
retrieval_evidence_keys[]
world_state_snapshot
todo_snapshot

stall_counter
oscillation_counter
retrieval_churn_counter

last_objective_progress_step

pending_postcondition
last_postcondition_result

run_contract_version
reasonfuse_enabled
```

State must live in `AgentSession`.

Do not rebuild it from prompt history.

Distinguish platform `agent_session_id` from the framework `AgentSession.session_id`;
record both alongside `conversation_id`. Define run lifetime explicitly: one
logical investigation across multiple turns and approval pause/resume, with a
new `run_id` only for an explicit new run. Persist a versioned, bounded,
JSON-serializable provider state. Do not keep credentials, full transcripts or a
second approval record. Test restoration using changed values and stable IDs,
not only constants initialized by `setdefault`.

The current validation provider already uses source ID/state namespace
`reasonfuse` for RF-STATE-001, counter 7 and middleware audit events. Avoid a
duplicate provider source ID or overwriting those regression markers. Give the
core a distinct versioned namespace (or a clearly nested core state) within the
same AgentSession. Validation markers are not the product's budget/progress state.

---

# 8. Canonical Tool Call Fingerprint

Implement canonical argument normalization.

Fingerprint:

```text
SHA256(
    tool_name
    +
    canonical_json(args)
)
```

Canonicalization should ensure equivalent dictionaries serialize identically.

Examples:

```json
{"a":1,"b":2}
```

and

```json
{"b":2,"a":1}
```

must produce the same fingerprint.

Preserve explicit differences that actually change tool semantics.

Use actual discovered native names and argument wrappers (currently
`operations___dns_resolution` and `operations___restart_service` with `{"body": ...}`).
Normalize recursively; pin behavior for arrays, booleans, numbers, null vs missing
and reject non-finite numbers. Do not silently sort order-sensitive arrays or
lowercase case-sensitive values. Version the normalization schema. Do not treat
an unknown/new parameter as equivalent to an omitted one.

---

# 9. Evidence Delta

Implement a structured evidence model.

Evidence Delta should represent new diagnostic information.

Examples of positive evidence:

```text
status changed from UNKNOWN → UNHEALTHY
dependency changed from UNKNOWN → DEGRADED
new distinct failure class observed
new source/citation materially changes the evidence set
```

Examples of zero evidence:

```text
same tool
same args
same result class
same external state
same retrieved sources
```

Do not use model prose length as evidence.

---

# 10. World-State Delta

Implement comparison of relevant external state.

Examples:

```text
service health
deployment version
database state
replica count
config version
restart generation
```

A relevant, independently observed external state change can be objective progress.
Timestamp, request ID, execution counter and random-ID changes alone are not.
An accepted restart request does not prove a health change or completed outcome.

World-state representation may be normalized into a small deterministic dictionary.

---

# 11. Retrieval Delta

Phase 1 has no Foundry IQ / retrieval implementation. Define the normalized
retrieval adapter explicitly; do not claim to reuse a validated adapter that does
not exist. A real Foundry IQ path requires separate integration evidence. For the
bounded Phase 2 detector scenario, a clearly labeled deterministic retrieval
fixture may be exposed through the existing managed Toolbox/local invocation
path. This proves churn containment on fixture evidence, not Foundry IQ quality
or retrieval integration. No custom RAG system or alternate MCP transport.

Prefer:

```text
source_keys[]
citation_ids[]
chunk_ids[] optional
scores[] optional
derived normalized content hashes optional
knowledge_base_version
```

Retrieval Delta is positive only when effective evidence changes materially.

Different query wording with equivalent evidence:

```text
Retrieval Delta = 0
```

---

# 12. Todo Delta

Capture:

```text
OPEN
IN_PROGRESS
COMPLETED
```

changes from TodoProvider.

Todo Delta is useful telemetry and planning context.

But:

```text
Todo Delta != Objective Progress
```

A Todo transition may be recorded while ReasonFuse remains STALLED.

---

# 13. Postcondition Delta

Implement postcondition observations for side effects.

At minimum Phase 2 must support:

```text
restart_service
→ required postcondition:
service_health == HEALTHY
```

Track:

```text
before state
accepted action
verification observation
final postcondition result
```

---

# 14. Progress Engine

Implement a deterministic progress decision.

Recommended conceptual output:

```text
objective_progress = true / false

signals:
  evidence_delta
  world_state_delta
  retrieval_delta
  postcondition_delta

planning_signal:
  todo_delta
```

Do not create a vague floating-point AI score.

A simple deterministic rule is acceptable:

```text
objective_progress = any(
    evidence_delta,
    world_state_delta,
    retrieval_delta,
    postcondition_delta
)
```

provided each delta is itself carefully defined.

---

# 15. Exact Loop Detector

Detect repeated identical tool-call fingerprints.

Example:

```text
dns_resolution("api")
dns_resolution("api")
dns_resolution("api")
```

with no objective progress.

Do not trip on the first legitimate retry.

Use Run Contract thresholds.

Expected result:

```text
EXACT_LOOP
```

---

# 16. Oscillation Detector

Detect alternating cycles such as:

```text
A → B → A → B
```

when no objective progress occurs.

At minimum detect period-2 oscillation.

Keep the implementation deterministic and bounded.

Expected result:

```text
OSCILLATING
```

Do not overengineer general sequence mining in Phase 2.

---

# 17. Retrieval Churn Detector

Detect repeated retrieval attempts that change query wording but not effective evidence.

Example:

```text
search("database failure")
→ sources {A,B}

search("db connectivity")
→ sources {A,B}

search("database issue")
→ sources {A,B}
```

with no new objective evidence.

Expected result:

```text
RETRIEVAL_CHURN
```

---

# 18. Useful Recheck Classifier

Required positive scenario:

```text
database_health()
 ↓
restart_service()
 ↓
database_health()
```

The second health check must be classified as useful because a side effect changed the world and verification is now required.

More precisely, a newly accepted side effect creates one bounded obligation to
verify the affected resource, even when health ultimately does NOT change.
Allow that necessary first postcondition read; do not grant unlimited rechecks
because a restart was attempted. Fresh relevant observed state may also justify
a recheck. Bind permission to action/resource/generation; unrelated service checks
must not consume or inherit it. Denied approvals do not create successful actions.

Required negative scenario:

```text
database_health()
 ↓
database_health()
 ↓
database_health()
```

with no state change.

This must be classified as wasteful repetition.

Recommended output:

```text
useful_recheck = true / false
reason = ...
```

Keep the reason deterministic.

---

# 19. Run Contract

Implement the frozen P0 contract:

```yaml
run_contract:
  max_steps: 12
  max_tool_calls: 10
  max_stalled_steps: 2
  max_oscillation_cycles: 2
  max_retrieval_churn: 3
  max_side_effects: 1
  required_objective_progress_interval: 2
  require_postcondition_for_side_effects: true
```

The exact defaults may be configuration, but tests must pin them.

Contract values and OFF/ON mode come from trusted run configuration, not model
prose or tool-result text. Persist their version with the run. Reject invalid
limits; a resumed run cannot change its contract to bypass an exhausted budget.

Run Contract must support:

```text
BUDGET_EXHAUSTED
```

when limits are exceeded.

Define counters and boundaries before implementation. Check the next dispatch
against tool/side-effect limits BEFORE execution (e.g. limit 1 permits one side
effect, blocks the second). Count actual attempts consistently; record failed,
blocked and denied proposals separately. Approval pause/resume is not a new run
and cannot reset budgets. An inconclusive or failed result cannot refill budgets.
Pin detector windows, threshold inclusivity, initial observation behavior and a
deterministic reason precedence in tests. Defaults may cause NO_PROGRESS before
an oscillation/churn threshold; targeted detector cases may use documented pinned
contracts to reach those thresholds. Retain separate tests of the default contract.

---

# 20. Behavioral Fuse

Implement deterministic containment.

Possible reasons:

```text
NO_PROGRESS
EXACT_LOOP
OSCILLATING
RETRIEVAL_CHURN
BUDGET_EXHAUSTED
POSTCONDITION_FAILED
```

When tripped, return a structured result.

Example:

```json
{
  "decision": "BLOCK",
  "trajectory_state": "STALLED",
  "fuse_reason": "NO_PROGRESS",
  "objective_progress": false,
  "step": 6
}
```

Do not merely stop with an exception.

Contain the run, not just one tool call: returning BLOCK while the model continues
calling tools forever is a failure. Use supported framework run/function middleware
termination, preserve the structured result and prove that no later external
dispatch occurs in the same run. Keep a deterministic failure reason even if the
model's final prose claims success. Outcome verification calls must remain in the
audited local function path and have bounded budget; no direct HTTP bypass around
enforcement. Reserve the required verification read within the contract explicitly.

Before dispatch, evaluate budgets and detectors against completed observations
and the proposed action. After dispatch, update progress from the authoritative
result. Do not invent a future result in order to justify a pre-call decision.
If a completed call trips the fuse, record that it executed and prove all later
dispatches are contained; do not mislabel that completed call as externally blocked.

---

# 21. ReasonFuse OFF Mode

Implement a runtime configuration:

```text
REASONFUSE_ENABLED=false
```

OFF mode must:

```text
observe telemetry if convenient
but NOT block the agent
```

This is required for the OFF/ON comparison.

Do not maintain two separate codebases.

Use the same agent and tools.

OFF disables ReasonFuse behavioral containment only. It must not disable native
human approval, RBAC, tool allowlists or test-environment safety constraints.
Use an independent, fixed test-harness ceiling/time limit to stop OFF experiments;
record HARNESS_STOP separately from FUSE_TRIPPED. Do not run unbounded loops.

---

# 22. ReasonFuse ON Mode

Implement:

```text
REASONFUSE_ENABLED=true
```

ON mode must enforce the Run Contract and Behavioral Fuse.

Same prompt.
Same model.
Same tools.
Same world.
Only ReasonFuse enforcement differs.

Use equivalent reset world-state snapshots, not the same counter epoch across
the OFF/ON pair: each reset creates a new epoch. Require an unchanged epoch only
within each individual before/action/after proof interval.

Keep release assignment constant: compare OFF and ON on an explicitly selected
backend with the same source/model/tools/contract and reset world, not random
stable-vs-candidate routing. Capture actual environment values and code hashes.
Pin trial count before execution and retain every attempt. Model behavior is
stochastic; a model that voluntarily stops is not evidence that the fuse blocked.
Use runtime decisions and independent external counters as the authority.

---

# 23. Operations API Phase 2 Behavior

Make the Operations API deterministic enough to reproduce core cases.

At minimum support:

```text
service_status
database_health
dns_resolution
restart_service
```

Add deterministic scenario/fault state.

Example:

```text
scenario = no_progress_dns

dns_resolution()
→ always INCONCLUSIVE
```

Outcome-failure scenario:

```text
restart_service()
→ HTTP 202 / accepted
→ service remains UNHEALTHY
```

Useful-recheck scenario:

```text
restart_service()
→ accepted
→ service becomes HEALTHY
→ next health check verifies success
```

Keep scenario state resettable.

Extend `tests/support/operations_api/` and `config/toolbox/` together; update
`scripts/create_toolbox.py` and the agent's explicit tool allowlist/approval modes.
Discover the deployed tools/list schema and record the new Toolbox version.
Keep administrator reset/counter endpoints protected; never send their key to the
model or include it in evidence. Report the operation as a simulated service state
transition, never a production restart. Record epoch plus before/after counters
and world state for each proof interval. An epoch change invalidates the result.
Run shared-counter scenarios sequentially and reset only BETWEEN scenarios.

---

# 24. Postcondition Registry

Implement a small registry.

At minimum:

```text
restart_service:
  verify with service_status
  expected:
    service_health == HEALTHY
```

Registry design should support later extension but remain simple.

---

# 25. Outcome Verifier

Required outcomes:

```text
OUTCOME_VERIFIED
POSTCONDITION_FAILED
OUTCOME_UNKNOWN
```

Phase 2 must prove:

```text
HTTP 202 accepted
≠
successful outcome
```

Outcome verification must perform a real postcondition check against the deterministic Operations API.

Check the exact resource acted upon with a fresh observation after acceptance.
Timeouts, unavailable/malformed observations and stale or mismatched-resource
responses produce OUTCOME_UNKNOWN, not verified success. Denial/cancellation must
not cause an operation or a claimed successful postcondition. Test all three
outcomes, including a native approval pause/resume. A failed verifier should
contain subsequent side effects with an explicit result, not blindly retry restart.

---

# 26. Core Live Scenarios

Implement at least these scenarios.

## Scenario A — OFF No-Progress

```text
ReasonFuse OFF
dns/search investigation repeats
agent is allowed to continue
```

Capture redundant behavior.

---

## Scenario B — ON No-Progress

Same world, same prompt, same tool behavior.

Expected:

```text
objective_progress = false
→ STALLED
→ FUSE_TRIPPED
```

---

## Scenario C — Exact Loop

Expected:

```text
EXACT_LOOP
→ BLOCK
```

---

## Scenario D — Oscillation

Expected:

```text
OSCILLATING
→ BLOCK
```

---

## Scenario E — Retrieval Churn

Expected:

```text
RETRIEVAL_CHURN
→ BLOCK
```

Use the explicitly scoped adapter/fixture in Section 11. Label this scenario
`LIVE_HOSTED_WITH_DETERMINISTIC_RETRIEVAL_FIXTURE` if it does not call Foundry IQ.
Its tool execution must still cross local Function Middleware and Foundry Toolbox.
Keep `Foundry IQ integration: NOT VERIFIED` visible; fixture PASS cannot erase it.
Do not silently replace a failed real retrieval run with a fixture and keep its
PASS label. Preserve the real-path failure and report the two evidence layers.

---

## Scenario F — Useful Recheck

Expected:

```text
restart
→ health recheck
→ ALLOW
```

No false positive.

---

## Scenario G — Outcome Failure

Expected:

```text
restart_service
→ accepted
→ postcondition fails
→ POSTCONDITION_FAILED
```

---

## Scenario H — Budget Exhaustion

Expected:

```text
Run Contract exceeded
→ BUDGET_EXHAUSTED
```

---

# 27. Telemetry

Emit structured OTel attributes/events where practical.

At minimum:

```text
reasonfuse.trajectory_state
reasonfuse.progress_state
reasonfuse.evidence_delta
reasonfuse.world_state_delta
reasonfuse.retrieval_delta
reasonfuse.todo_delta
reasonfuse.postcondition_delta
reasonfuse.useful_recheck
reasonfuse.failure_type
reasonfuse.fuse_reason
reasonfuse.contract_version
```

Do not build dashboards in Phase 2.

Keep body/message-content capture disabled and metadata diagnostics enabled.
Do not log raw transcripts/tool payloads, tokens, connection strings or affinity
cookies to broad production telemetry. Phase-specific synthetic evidence may
include bounded, nonsecret state and arguments. Use hashes/names for cookies.

---

# 28. Test Strategy

Implement:

```text
unit tests
+
integration tests
+
live Hosted Agent scenarios
```

Unit tests must cover detector edge cases.

Integration tests must prove the middleware/state flow.

Live scenarios must prove the P0 behavior in the validated Microsoft runtime.

Keep existing Phase 1 entry points runnable as regressions after construction.
Do not keep the Phase 1 validation instruction "perform each diagnostic only once"
as the Phase 2 scenario driver: it suppresses the very loops OFF must expose.
Separate the validation profile from the core scenario profile explicitly, without
changing native history/approval/tool ownership. Document which profile was deployed.
Phase 1 deterministic probes may not serve as substitutes for Phase 2 core decisions.

Add local negative tests for canonicalization edge cases, Todo-only progress,
unrelated/noisy world changes, bounded useful-recheck permission, detector reason
precedence, post-trip calls, malformed outcomes, and approval resume budgets.
Local tests remain `LOCAL_UNIT` / `LOCAL_INTEGRATION`, never live PASS.

---

# 29. Phase 2 Required Acceptance Tests

Required:

```text
[ ] OFF mode does not block

[ ] ON mode blocks no-progress behavior

[ ] Exact Loop detector trips

[ ] Oscillation detector trips

[ ] Retrieval Churn detector trips

[ ] Useful Recheck scenario is preserved

[ ] Todo-only change does not count as objective progress

[ ] Run Contract budget exhaustion trips

[ ] restart_service accepted + unhealthy
    → POSTCONDITION_FAILED

[ ] restart_service accepted + healthy
    → OUTCOME_VERIFIED

[ ] ReasonFuse state persists through the run

[ ] local Function Middleware remains in the enforcement path

[ ] native approval, denial, argument binding and same-action replay remain safe

[ ] containment stops subsequent dispatch rather than merely returning BLOCK once

[ ] timeout/stale/mismatched observations produce OUTCOME_UNKNOWN

[ ] OFF/ON evidence distinguishes harness stop, voluntary model stop and fuse stop
```

---

# 30. Evidence Capture

For every core scenario capture:

```text
scenario name
ReasonFuse OFF/ON
run_id
conversation_id
agent_session_id
tool sequence
objective progress signals
detector state
fuse decision
postcondition result
trace/request ID if available
exit result
```

Save under:

```text
evidence/phase-02-core/<UTC-batch>/
```

Do not store secrets.

Index each requirement by evidence layer, command, UTC timestamp, exit code,
repo-relative artifact path and SHA-256. Capture deployed source/ZIP manifests,
embedded build identity, stable/candidate versions, dependencies, actual tool
schema, scenario epoch and before/after counters. Use `scripts/deploy.ps1`'s
audited native packaging and serial release readback; do not revert to unverified
parallel agent deployment. Preserve the retained Phase 1 acceptance evidence and
final report; do not recreate the removed historical reports.
If the package membership changes, update the source-identity audit explicitly.

---

# 31. Core Construction Report

Create `docs/phases/phase-02-core/report.md` and a separate
`docs/phases/phase-02-core/open-questions.md`. Use PASS / FAIL / NOT VERIFIED
for each evidence layer, and include failures, corrective diffs and retests.
Report template:

```text
# Phase 2 ReasonFuse Core Report

## Environment
...

## Core Modules Implemented
...

## Scenario A — OFF No-Progress
PASS / FAIL
Evidence: ...

## Scenario B — ON No-Progress
PASS / FAIL
Evidence: ...

## Scenario C — Exact Loop
PASS / FAIL

## Scenario D — Oscillation
PASS / FAIL

## Scenario E — Retrieval Churn
PASS / FAIL

## Scenario F — Useful Recheck
PASS / FAIL

## Scenario G — Outcome Failure
PASS / FAIL

## Scenario H — Budget Exhaustion
PASS / FAIL

## Outcome Verification
OUTCOME_VERIFIED case: PASS / FAIL
POSTCONDITION_FAILED case: PASS / FAIL

## Architecture Change Required?
YES / NO

## Remaining Questions and Evidence Boundaries
Foundry IQ integration: VERIFIED / NOT VERIFIED
Production restart: NOT VERIFIED (deterministic test service only)
Phase 1 regression result and evidence: ...
Unresolved blockers and exact reproduction commands: ...

## Phase 2 Result
PASS / BLOCKED
```

---

# 32. What Phase 2 Must NOT Do

Do not spend Phase 2 on:

```text
100-scenario benchmark
300-run benchmark
confusion matrix
APIM canary polish
Judge Mode final UI
user testing
video production
AI Red Teaming
advanced Foundry Evaluation
release automation
multi-region
production dashboards
```

Those belong to later phases.

---

# 33. Construction Completion Gate

Construction is complete when:

```text
[ ] all core modules exist
[ ] unit tests exist
[ ] integration tests exist
[ ] live scenario scripts exist
[ ] OFF/ON configuration exists
[ ] deterministic Operations API scenario state exists
[ ] Outcome Verifier is wired
[ ] telemetry exists
[ ] reset script works
[ ] construction report contains actual test outcomes and evidence links
[ ] open-questions report contains remaining issues or explicitly states none in scope
[ ] full Phase 1 regression suite and supplementary checks rerun on the evolved runtime
[ ] all Phase 2 live scenarios executed, not merely supplied as scripts
[ ] reset verifies scoped test-session cleanup, zero counters and scenario baseline
```

At construction completion, state:

```text
PHASE 2 CONSTRUCTION COMPLETE
READY FOR INDEPENDENT VALIDATION
```

Do not self-award Phase 2 PASS unless the separate verification procedure is executed.

If any mandatory construction/live gate is missing, report
`PHASE 2 CONSTRUCTION: BLOCKED` with exact evidence and next action. A report
template or collection of passing unit tests alone is not construction completion.
Do not commit/push, expand cloud architecture or implement later phases as part
of this prompt. Retain Azure resources for independent validation.
