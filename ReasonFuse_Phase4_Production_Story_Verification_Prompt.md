# ReasonFuse Phase 4 — Production Story Verification Prompt

> **Purpose:** Independently verify that the Phase 4 production story is real, release-sticky, traceable, demoable, and competition-ready within an explicit bounded P0 scope.  
> **Audience:** GPT-6 Astra / independent validation agent  
> **Phase:** 4 — Production Story  
> **Role:** Validator, not implementer  
> **Prerequisite:** Phase 3 = PASS  
> **Primary Exit Gate:** `Complete clean-start E2E + Native Foundry IQ + APIM canary + Judge Mode + tracing + rollback PASS`
>
> **Scope rule:** Phase 4 P0 uses the budget-controlled `15 scenarios × 1 run` baseline. The profile is fixed at this size for the competition project.

---

# 1. Mission

Your job is to determine whether the production story is genuine.

Do not validate merely that:

```text
Terraform applies
APIM exists
Judge Mode renders
a screenshot looks correct
```

You must prove the real end-to-end behavior.

Return:

```text
Stable/Candidate Setup     PASS / FAIL
APIM Weighted Canary       PASS / FAIL
Session Affinity           PASS / FAIL
SSE Pass-Through           PASS / FAIL
Release Lineage            PASS / FAIL
Tracing                    PASS / FAIL
Judge Mode                 PASS / FAIL
OFF/ON Demo                PASS / FAIL
Unknown Path Demo          PASS / FAIL
Outcome Failure Demo       PASS / FAIL
Candidate Regression       PASS / FAIL
Rollback                   PASS / FAIL
Repeatability              PASS / FAIL

PHASE 4 RESULT:
BOUNDED P0 PASS / PASS / BLOCKED
```

Use `BOUNDED P0 PASS` when every mandatory runtime gate in Section 32 passes within the declared scope. Use unqualified `PASS` only when the optional extended evidence package has also been executed. Use `BLOCKED` when a mandatory production-story capability fails after reasonable diagnostic work.

---

# 2. Validation Principles

## Principle 1 — Real Routing, Not Simulated Labels

Do not accept a UI field that says:

```text
release_role = candidate
```

unless APIM actually routed the request to Candidate.

---

## Principle 2 — Same Conversation Must Stay Release-Sticky

The same run must not bounce between Stable and Candidate.

---

## Principle 3 — Judge Mode Must Reflect Runtime State

Do not accept hard-coded demo values.

---

## Principle 4 — Rollback Must Actually Change Traffic

A rollback button or script is not sufficient.

You must verify new traffic behavior after rollback.

The mandatory rollback assertion is that new sessions route Stable after Candidate reaches weight zero. Existing-session behavior is outside the frozen competition scope.

---

# 3. Pre-Validation Audit

Record:

```text
date/time
Azure subscription
Foundry project
region

Stable agent version
Candidate agent version

model version
prompt versions
toolbox version
knowledge base version
Run Contract version

APIM instance
APIM backend pool configuration

agent-framework version
foundry-hosting version
azure-ai-projects version

git commit
```

Confirm:

```text
PHASE3_REPORT.md
→ PASS
```

Run Phase 4 preflight.

---

# 4. Stable / Candidate Matrix Audit

Verify both releases exist independently.

Confirm:

```text
release_role stable
release_role candidate
```

Confirm controlled comparison:

```text
same model
same Toolbox
same KB
same Run Contract
same environment
```

Document intended difference.

If multiple uncontrolled variables differ:

```text
Stable/Candidate Setup = FAIL
```

---

# 5. APIM Weighted Canary Validation

Inspect APIM configuration.

Required:

```text
Stable = 95
Candidate = 5
```

Use multiple new sessions/clients.

Do not require exact 95/5 over a tiny sample.

The purpose is to verify both weighted backends are live and selectable.

Record observed assignment counts.

If practical, use enough new sessions to observe Candidate at least once.

Do not alter weights merely to fake production behavior in the final report.

A temporary validation-only higher Candidate weight may be used only if clearly isolated and reset afterward.

---

# 6. Session Affinity Validation

Use one persistent HTTP client/session.

Perform at least 5 turns in the same conversation.

Record each:

```text
turn
release_role
affinity cookie/header
conversation_id
```

Required:

```text
same release_role every turn
```

Invalid:

```text
Stable
Candidate
Stable
```

---

# 7. Fresh Client Negative Control

Create a new client/session with no previous affinity state.

Verify it receives an independent assignment.

This proves stickiness is session-based rather than globally pinned.

---

# 8. Affinity Preservation in Judge Mode

Run the actual Judge Mode client.

Confirm it also preserves affinity across the multi-turn demo.

Do not validate only the standalone APIM test client.

---

# 9. SSE Pass-Through Validation

Use the actual APIM endpoint.

Run a streaming response.

Capture:

```text
chunk contents
chunk receive timestamps
final completion timestamp
```

Required:

```text
first chunk arrives before full response completion
multiple chunks arrive incrementally
```

Inspect APIM policy/config:

```text
buffer-response = false
response caching = OFF
streaming body diagnostics = OFF
```

If the full body arrives at once:

```text
SSE Pass-Through = FAIL
```

---

# 10. Release Lineage Validation

For a Stable run and a Candidate run, inspect telemetry.

Required lineage:

```text
run_id
trace_id
conversation_id
agent_session_id

release_role
agent_version
model_version
prompt_version
toolbox_version
knowledge_base_version
reasonfuse_contract_version
```

Framework version lineage should also be available where implemented.

---

# 11. Foundry Tracing Validation

Run one ReasonFuse containment scenario.

Trace must show enough evidence to reconstruct:

```text
tool sequence
objective-progress signals
fuse reason
containment
```

Required key attributes:

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

Do not fail for cosmetic trace-view issues.

Fail if core ReasonFuse decisions are not observable.

---

# 12. Application Insights Validation

Confirm traces/events arrive in Application Insights or the selected Foundry monitoring sink.

Query one known `trace_id`.

Verify the expected ReasonFuse attributes are present.

---

# 13. Judge Mode Runtime Integrity

Run Judge Mode against a real scenario.

Verify each displayed field maps to actual runtime data.

At minimum:

```text
Safety
Authorization
ReasonFuse decision
Trajectory
Objective Progress
Evidence Delta
World-State Delta
Retrieval Delta
Todo Delta
Postcondition Delta
Useful Recheck
Fuse reason
containment latency
release role
```

Spot-check values against trace/raw run evidence.

Any hard-coded mismatch:

```text
Judge Mode = FAIL
```

---

# 14. Judge Mode Comprehension Test

Without reading internal implementation, inspect the screen.

It should make the core distinction clear:

```text
Safety PASS
Authorization ALLOW
ReasonFuse BLOCK
```

and:

```text
Planning changed.
Reality did not.
```

If the UI is technically correct but too confusing to understand, mark:

```text
Judge Mode = PARTIAL
```

and require a wording/layout fix before PASS.

---

# 15. Demo A — OFF / ON Validation

Run the same deterministic no-progress scenario twice.

OFF:

```text
ReasonFuse disabled
→ redundant execution continues
```

Reset.

ON:

```text
ReasonFuse enabled
→ no-progress contained
```

Confirm:

```text
same model
same prompt
same tools
same world state
```

Capture:

```text
tool calls
steps
containment
```

Required:

```text
OFF continues
ON contains
```

---

# 16. Demo B — Unknown Correct Path Validation

Run a scenario where multiple investigation sequences are legitimate.

Confirm ReasonFuse does not require one exact path.

Required:

```text
agent may choose a different valid path
objective progress continues
ReasonFuse does not block healthy investigation
```

If the demo only succeeds because the agent follows a benchmarked expected sequence:

```text
Unknown Path Demo = FAIL
```

---

# 17. Demo C — Outcome Failure Validation

Run:

```text
restart_service
→ approval
→ accepted / HTTP 202
→ service remains unhealthy
```

Required:

```text
Authorization = ALLOW
Execution accepted = true
Outcome = POSTCONDITION_FAILED
```

Judge Mode and trace must show this distinction.

Primary invariant:

```text
Execution success is not outcome success.
```

---

# 18. Demo D — Candidate Regression Validation

Force deterministic fault:

```text
dns_resolution
→ INCONCLUSIVE
```

Run Stable.

Expected:

```text
fallback / continued productive investigation
```

Run Candidate.

Expected:

```text
repeated DNS investigation
→ no objective progress
→ ReasonFuse trips
```

Confirm both use:

```text
same Toolbox
same KB
same model
same Run Contract
```

---

# 19. Candidate Regression Causality Audit

Confirm the Candidate regression is seeded in:

```text
agent behavior / prompt / agent version
```

not secretly injected into ReasonFuse itself.

ReasonFuse must remain the same reliability layer across Stable and Candidate.

---

# 20. Rollback Validation

Trigger the defined rollback.

Required state after rollback:

```text
Candidate weight = 0
Stable weight = 100
```

or equivalent effective removal.

Create new clients/sessions.

Required:

```text
all new sessions route Stable
```

Record APIM config/evidence.

---

# 21. Rollback Recovery Check

After Candidate removal:

```text
run a clean Stable scenario
```

Required:

```text
service remains operational
Stable traffic succeeds
```

Rollback must not break the whole endpoint.

---

# 23. Repeatability Validation

Run each signature demo at least 3 times after reset:

```text
OFF/ON × 3
Unknown Path × 3
Outcome Failure × 3
Candidate Regression × 3
```

The exact LLM path may vary.

The expected ReasonFuse classification/outcome should remain stable.

---

# 24. Demo Script Audit

Inspect demo scripts.

Required:

```text
reset
preflight
scenario configuration
execution
evidence capture
PASS/FAIL
```

The operator should not need to manually repair state between runs.

---

# 25. Clean-Start E2E Validation

From a clean operational state:

```text
preflight
verify Stable/Candidate release matrix
verify Native Foundry IQ for Stable and Candidate
start Judge Mode
verify APIM 95/5, affinity and incremental SSE
run OFF/ON
run Unknown Correct Path
run Outcome Failure
run Candidate Regression
rollback to Stable 100 / Candidate 0
create a new session
confirm Stable
```

This should work without manual code edits.

The clean-start run must record the first warm-up failure, if any, separately from the final stabilized result. A transient platform warm-up response must not be silently counted as either a product failure or a product pass.

---

# 26. Production Narrative Audit

Check that implementation and demo preserve the responsibility boundary:

```text
Safety
Authorization
Planning
Objective Progress
Outcome Verification
```

Do not allow Judge Mode or README to claim ReasonFuse replaces:

```text
Guardrails
RBAC
approval
Foundry evaluation
```

---

# 27. Benchmark Evidence Integration

Judge Mode / demo may display selected Phase 3 results.

Verify they match `PHASE3_REPORT.md`.

Do not recompute marketing numbers differently in Phase 4.

The Phase 4 benchmark profile is fixed at `15 scenarios × 1 run`. Do not expand
the profile during verification.

---

# 28. Live Metrics Validation

If live metrics are exposed, verify at least:

```text
trip reason
containment latency
release role
postcondition failure
healthy completion where available
```

Do not require a large dashboard.

---

# 29. Failure Classification

Classify Phase 4 failures as:

```text
APIM_ROUTING_ERROR
AFFINITY_ERROR
SSE_BUFFERING_ERROR
IDENTITY_ERROR
TRACE_LINEAGE_ERROR
JUDGE_MODE_DATA_ERROR
DEMO_RESET_ERROR
ROLLBACK_ERROR
RELEASE_COMPARABILITY_ERROR
ENVIRONMENT_ERROR
REASONFUSE_CORE_REGRESSION
ARCHITECTURE_ASSUMPTION_FAILURE
```

Do not reopen architecture for ordinary UI or Terraform bugs.

---

# 30. Evidence Requirements

For each major PASS claim, preserve:

```text
commands
timestamps
APIM configuration
affinity state
release role
trace IDs
conversation IDs
Judge Mode runtime-state capture
tool sequences
ReasonFuse decisions
rollback evidence
```

UI screenshots are optional presentation evidence. Their absence must not invalidate a bounded P0 runtime result when the runtime-state payload and trace evidence are available.

Do not store secrets.

---

# 31. PHASE4_REPORT.md

Update:

```text
# Phase 4 Production Story Validation Report

## Scope
Bounded P0 / extended validation

## Environment
...

## Stable / Candidate Matrix
PASS / FAIL

## APIM Weighted Canary
PASS / FAIL
Evidence:

## Session Affinity
PASS / FAIL
Evidence:

## SSE
PASS / FAIL
Evidence:

## Release Lineage
PASS / FAIL

## Foundry Tracing / App Insights
PASS / FAIL

## Native Foundry IQ
PASS / FAIL

## Hosted Cold-Start
PASS / FAIL

## Judge Mode
PASS / FAIL

## Demo A — OFF / ON
PASS / FAIL

## Demo B — Unknown Correct Path
PASS / FAIL

## Demo C — Outcome Failure
PASS / FAIL

## Demo D — Candidate Regression
PASS / FAIL

## Rollback
PASS / FAIL

## Repeatability
PASS / FAIL

## Clean-Start E2E
PASS / FAIL

## Optional Extensions
Screenshots / larger hosted repetition / existing-session semantics

## Architecture Change Required?
YES / NO

## Phase 4 Result
BOUNDED P0 PASS / PASS / BLOCKED
```

---

# 32. Phase 4 PASS Gate

Return:

```text
PHASE 4 RESULT: BOUNDED P0 PASS
```

when all mandatory P0 conditions are true:

```text
[ ] Stable/Candidate releases independently exist

[ ] release comparison is controlled

[ ] APIM weighted routing works

[ ] same persistent client stays release-sticky

[ ] fresh client receives independent assignment

[ ] actual Judge Mode client preserves affinity

[ ] SSE arrives incrementally through APIM

[ ] release lineage is observable

[ ] Stable and Candidate each make the real Native Foundry IQ MCP call

[ ] Foundry Tracing captures ReasonFuse decisions

[ ] App Insights / monitoring sink receives trace data

[ ] Judge Mode is driven by real runtime data

[ ] Judge Mode clearly distinguishes Safety / Authorization / ReasonFuse

[ ] OFF/ON demo PASS

[ ] Unknown Correct Path demo PASS

[ ] Outcome Failure demo PASS

[ ] Candidate Regression demo PASS

[ ] rollback removes Candidate traffic for new sessions

[ ] Stable remains healthy after rollback

[ ] all four signature demos are repeatable

[ ] clean-start E2E sequence PASS

[ ] hosted-session cold-start lifecycle PASS, or the declared platform limitation is explicitly recorded

[ ] no Phase 2/3 core regression discovered

[ ] no frozen architecture assumption failed
```

The bounded P0 result is complete with the fixed `15 scenarios × 1 run`
profile. Presentation screenshots are separate, non-runtime material.

Return:

```text
PHASE 4 RESULT: PASS
```

only when the bounded P0 conditions above pass and the declared optional extensions have also been completed. Never upgrade `BOUNDED P0 PASS` to unqualified `PASS` merely because the local construction path or a screenshot looks correct.

---

# 33. BLOCKED Gate

Return:

```text
PHASE 4 RESULT: BLOCKED
```

if any competition-critical production-story capability fails after reasonable diagnostic work.

Examples:

```text
conversation hops between releases
Judge Mode is hard-coded
SSE is buffered
Candidate regression is not causally isolated
rollback does not change real traffic
Outcome Failure is not visible
tracing cannot connect decision to release
```

---

# 34. Final Validator Instruction

Phase 4 should make the project feel like a production system, not a research notebook.

The final proof should be:

```text
A working agent
+
runtime containment
+
real-world outcome verification
+
bounded benchmark evidence
+
versioned releases
+
sticky canary
+
traceable decisions
+
clear Judge Mode
+
rollback
```

The result must state the evidence boundary explicitly. Phase 4 is complete for P0 when the real hosted path is proven; optional scale, screenshots, and presentation packaging must not be presented as if they were mandatory runtime gates.

Do not optimize for more features.

Optimize for a clean, undeniable end-to-end story.
