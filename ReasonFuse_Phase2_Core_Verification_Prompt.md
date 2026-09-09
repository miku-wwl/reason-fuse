# ReasonFuse Phase 2 — Core Verification Prompt

> **Purpose:** Independently verify that the Phase 2 ReasonFuse P0 core actually works on the validated Microsoft runtime.  
> **Audience:** GPT-6 Astra / independent validation agent  
> **Phase:** 2 — ReasonFuse Core  
> **Role:** Validator, not implementer  
> **Prerequisite:** Phase 1 = PASS  
> **Primary Exit Gate:** `OFF/ON + Outcome Verification PASS`

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

---

## Postcondition Delta

Create a successful external state transition.

Required:

```text
Postcondition Delta = positive
```

---

# 8. Exact Loop Validation

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
service_status
database_health
service_status
database_health
```

with no objective progress.

Expected:

```text
OSCILLATING
→ BLOCK
```

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
max_tool_calls
max_stalled_steps
max_side_effects
required_objective_progress_interval
```

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

If Phase 2 implements timeout/inconclusive verification, validate:

```text
verification unavailable or inconclusive
→ OUTCOME_UNKNOWN
```

If not implemented in Phase 2, record as deferred, but failure/success paths remain mandatory.

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
```

These three core scenarios must pass from a clean start.

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
```

Architecture should only be reopened for the final category.

Do not redesign because a detector implementation is wrong.

---

# 22. Required Phase 2 Evidence

For every required scenario capture:

```text
scenario ID/name
OFF / ON
run_id
conversation_id
agent_session_id

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
evidence/phase2/
```

---

# 23. Phase 2 Report

Update:

```text
PHASE2_REPORT.md
```

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

## Todo-Only Progress Negative Control
PASS / FAIL

## Middleware Enforcement
PASS / FAIL

## Determinism Repeats
PASS / FAIL

## Clean-Start Revalidation
PASS / FAIL

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

[ ] critical tool blocking prevents real execution

[ ] detector results are stable across repeated resets

[ ] clean-start OFF/ON + Useful Recheck + Outcome Failure PASS

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
