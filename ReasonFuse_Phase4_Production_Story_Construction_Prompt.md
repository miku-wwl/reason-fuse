# ReasonFuse Phase 4 — Production Story Construction Prompt

> **Purpose:** Build the production-grade release, observability, Judge Mode, and end-to-end demo layer on top of the validated Phase 3 benchmarked ReasonFuse core.  
> **Audience:** GPT-6 Astra / coding agent  
> **Phase:** 4 — Production Story  
> **Expected effort:** 6–9 hours  
> **Prerequisite:** Phase 3 Evidence & Benchmark = **PASS**  
> **Architecture status:** FROZEN — no redesign  
> **Primary Exit Gate:** `Stable/Candidate + APIM sticky canary + native Foundry IQ retrieval + tracing + Judge Mode + cold-start recovery + complete E2E demo PASS`

---

# 1. Mission

Phase 4 is not about adding new ReasonFuse intelligence.

Phase 4 turns the validated ReasonFuse core and benchmark evidence into a production-shaped story that judges can understand quickly.

Your job is to implement and prove:

```text
1. Stable / Candidate release model
2. APIM weighted sticky canary
3. Same-conversation release affinity
4. SSE streaming through APIM
5. Foundry Tracing / Application Insights lineage
6. Judge Mode
7. Candidate regression scenario
8. Rollback / traffic removal path
9. Clean end-to-end demo flow
10. Competition-facing production narrative
11. Native Foundry IQ retrieval path with versioned source/citation evidence
12. Forced platform cold-start recovery with state/history evidence
```

The product core must remain unchanged except for bug fixes required by integration.

---

# 2. Hard Prerequisite

Before construction, inspect:

```text
PHASE3_REPORT.md
```

Required:

```text
PHASE 3 RESULT: PASS
```

At minimum:

```text
15 curated Agentathon scenarios
15 valid runs
confusion matrix verified
Recall / Precision / FPR / FNR verified
Healthy Completion verified
Useful Recheck Preservation verified
Postcondition Failure Detection verified
10,000-event microbenchmark verified
```

If Phase 3 is not PASS:

```text
STOP
```

Do not build a production story around unverified evidence.

---

# 3. Frozen Production Architecture

Do not redesign this:

```text
User / Judge UI
 ↓
Azure API Management
 ├─ Authentication
 ├─ Weighted 95/5
 ├─ Session Affinity
 ├─ SSE pass-through
 └─ no streaming body buffering
 ↓
Foundry Hosted Agent
 ├─ Stable version
 └─ Candidate version
 ↓
Native Foundry IQ knowledge source / retrieval path
 (version-pinned; real connection and citations)
 ↓
ResponsesHostServer
history_source="agent_server"
 ↓
Microsoft Agent Framework Agent
 ├─ TodoProvider
 ├─ AgentModeProvider
 ├─ AgentSession
 ├─ Tool Approval
 └─ ReasonFuse Middleware
      ↓
Foundry Toolbox / Operations API
      ↓
Outcome Verifier
      ↓
OpenTelemetry
      ↓
Foundry Tracing
      ↓
Application Insights
```

Release flow:

```text
Versioned Dataset
 ↓
evaluate_agent(num_repetitions=1)
 ↓
LocalEvaluator
 ↓
PASS
 ↓
APIM Sticky Canary
 ├─ 95% Stable
 └─ 5% Candidate
 ↓
ReasonFuse Live Metrics
 ↓
PROMOTE / ROLLBACK
```

---

# 4. Non-Negotiable Rules

## Rule 1 — No New Architecture

Do not add:

```text
new database
new queue
new control plane
multi-agent layer
new orchestration framework
custom tracing backend
custom release platform
custom canary router
```

Use the frozen stack.

---

## Rule 2 — Stable and Candidate Must Be Comparable

For controlled release testing, preserve:

```text
same model
same prompt family
same Toolbox version
same knowledge base version
same Run Contract version
same environment
```

Only the intended candidate behavior should differ.

For the Phase 4 native retrieval path, Stable and Candidate must use the same
Foundry IQ connection, knowledge source, index/data-source version, retrieval
permissions, and query contract unless the experiment explicitly tests a
retrieval-version change. Phase 4 is not a license to silently substitute the
existing deterministic `retrieval_fixture` for native Foundry IQ evidence.

---

## Rule 3 — No Per-Turn Random Routing

This is forbidden:

```text
Turn 1 → Stable
Turn 2 → Candidate
Turn 3 → Stable
```

A conversation/run must stay release-sticky.

---

## Rule 4 — Judge Mode Is Explanation, Not Enforcement

Judge Mode must display ReasonFuse decisions.

It must not become a second hidden decision engine.

---

# 5. Phase 4 Deliverables

Implement:

```text
Stable Hosted Agent release
Candidate Hosted Agent release

APIM weighted backend pool
APIM session affinity
APIM SSE pass-through

persistent client session
affinity preservation

release lineage telemetry

Judge Mode
candidate regression scenario
rollback / traffic removal action

E2E demo script
production-story screenshots/evidence
PHASE4_REPORT.md
```

---

# 6. Stable / Candidate Release Setup

Create two versioned agent releases:

```text
Stable
Candidate
```

Record for both:

```text
agent_version
release_role
model_version
prompt_version
toolbox_version
knowledge_base_version
reasonfuse_contract_version
agent_framework_version
foundry_hosting_version
azure_ai_projects_version
```

Recommended controlled difference:

```text
Stable:
If DNS is inconclusive:
fallback to service_status()

Candidate:
If DNS is inconclusive:
repeat DNS investigation before fallback
```

Use this seeded regression only if it can be implemented without altering the ReasonFuse core.

---

# 7. Toolbox Version Pinning

For canary comparison:

```text
Stable Toolbox version = Candidate Toolbox version
```

Use one immutable/frozen Toolbox version where possible.

Do not allow:

```text
Stable → Toolbox v3
Candidate → Toolbox v4
```

during the controlled experiment.

---

# 8. Knowledge Base Version Pinning

Likewise:

```text
Stable knowledge_base_version
=
Candidate knowledge_base_version
```

unless the experiment is explicitly about retrieval-version changes, which Phase 4 is not.

---

# 8A. Native Foundry IQ Retrieval Construction

Phase 4 must construct a real native Foundry IQ retrieval path. The existing
deterministic `retrieval_fixture` is useful for Phase 2/3 behavior evidence,
but it must not be presented as Foundry IQ.

Construct and record, using the frozen Azure/Foundry project scope:

```text
Foundry project connection
knowledge source / index / data source
RBAC and managed-identity access
knowledge_base_version
retrieval query contract
returned source keys and citations
content hashes or equivalent source identity
retrieval trace/run/session identifiers
```

The construction must include at least one reproducible query whose answer is
grounded in the configured native source. Save the request, retrieved source
identity, citation metadata, version, and the corresponding hosted trace.

Required construction rules:

```text
do not call retrieval_fixture and label it Foundry IQ
do not use an untracked local file as the native knowledge source
do not omit the connection or data-source identity
do not claim retrieval success without source/citation evidence
do not change Stable/Candidate retrieval inputs during a release comparison
```

If the current subscription has no eligible native knowledge source, record the
exact provisioning or RBAC blocker in the Phase 4 open-questions report. Do
not silently downgrade this item to a fixture PASS.

---

# 8B. Forced Platform Cold-Start Construction

Phase 4 must construct a real cold-start recovery procedure for the deployed
hosted agent/runtime. A fresh HTTP client or a new browser session is not a
platform cold-start and may only be recorded as a separate recovery proxy.

The procedure must:

```text
1. create a conversation and establish authoritative runtime state
2. record response/session/history/ReasonFuse state and trace identity
3. force a bounded platform restart, recycle, or equivalent cold-start event
4. wait for the deployment to become healthy
5. continue the same conversation with a fresh client
6. call read_runtime_state and inspect canonical conversation history
7. verify state restoration, turn continuity, and no counter reset/leak
8. capture pre-restart and post-restart trace/run/session identifiers
```

Use only a bounded test conversation and restore the intended Stable release
after the procedure. Record the actual restart mechanism, timestamps,
deployment/instance identity, health checks, and any platform limitation. If
the platform cannot be safely forced to cold-start in the current environment,
the result is `NOT VERIFIED`, not a PASS inferred from fresh-client recovery.

---

# 9. APIM Weighted Pool

Configure:

```text
Stable weight    = 95
Candidate weight = 5
```

Use Terraform where practical.

If the pinned AzureRM provider does not expose the required pool/session-affinity fields:

```text
use AzAPI
```

Do not redesign around the limitation.

---

# 10. APIM Session Affinity

Enable backend/session affinity.

Required behavior:

```text
new session/client
→ assigned Stable or Candidate

same session/client
→ stays on same backend
```

Do not create a new stateless HTTP client for every turn.

---

# 11. Judge / Benchmark Client Affinity

The client used for:

```text
Judge Mode
demo
candidate regression
multi-turn conversation
```

must use one persistent HTTP session/client.

Preserve:

```text
affinity cookie
auth state
conversation state
```

for the lifetime of one conversation/run.

---

# 12. SSE Pass-Through

Required APIM behavior:

```text
forward-request:
  buffer-response = false

response caching:
  OFF

streaming body diagnostics:
  OFF

metadata telemetry:
  ON
```

The client must visibly receive streamed chunks incrementally.

Do not simulate streaming locally after a buffered response.

---

# 13. Authentication / Identity Boundary

Keep this distinction visible:

```text
APIM release affinity
→ Which backend release?

Foundry user/session isolation
→ Whose data/conversation?
```

Do not mix them.

If the current implementation uses user identity end-to-end, preserve it.

If a service identity is used in the middle tier, do not pretend Foundry sees the original user unless trusted propagation is actually implemented.

Do not expand into P1 identity propagation work unless already available.

---

# 14. Release Lineage Telemetry

Every request/run should emit enough lineage to answer:

```text
Which release handled this?
Which model?
Which prompt?
Which Toolbox?
Which KB?
Which ReasonFuse contract?
Which framework version?
```

At minimum:

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

agent_framework_version
foundry_hosting_version
azure_ai_projects_version
```

---

# 15. Foundry Tracing / Application Insights

Use:

```text
ReasonFuse
 ↓ OTel
Foundry Tracing
 ↓
Application Insights
```

Do not build a custom tracing platform.

Capture key ReasonFuse attributes:

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

---

# 16. Judge Mode

Build a compact competition-facing view.

The primary screen should answer:

```text
Was it safe?
Was it authorized?
Was it making objective progress?
Was it blocked?
Why?
```

Recommended structure:

```text
┌──────────────────────────────────────────────┐
│                 ReasonFuse                   │
│                                              │
│ Safety                    PASS               │
│ Authorization             ALLOW              │
│ ReasonFuse                BLOCK              │
│                                              │
│ Trajectory                NO_PROGRESS        │
│ Objective Progress        0                  │
│ Evidence Delta            0                  │
│ World-State Delta         0                  │
│ Retrieval Delta           0                  │
│ Todo Delta               +1                  │
│ Useful Recheck            NO                 │
│                                              │
│ Planning changed. Reality did not.           │
│                                              │
│ FUSE TRIPPED              2.8s               │
└──────────────────────────────────────────────┘
```

The exact visual style may vary.

The semantics must not.

---

# 17. Judge Mode Data Source

Judge Mode must consume real runtime telemetry / structured ReasonFuse results.

Do not hard-code:

```text
PASS
ALLOW
BLOCK
```

for demo scenarios.

The display must be driven by actual run state.

---

# 18. Judge Mode Required Fields

At minimum display:

```text
Safety
Authorization
ReasonFuse decision

Trajectory state
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

Optional:

```text
agent version
trace ID
tool sequence
```

Keep advanced details secondary.

---

# 19. Candidate Regression Scenario

Use the controlled regression:

```text
dns_resolution()
→ always INCONCLUSIVE
```

Stable expected behavior:

```text
DNS inconclusive
→ fallback to service_status()
→ objective investigation continues
```

Candidate expected behavior:

```text
DNS inconclusive
→ repeat DNS investigation
→ no new evidence
→ ReasonFuse detects no progress
→ FUSE_TRIPPED
```

This scenario should demonstrate:

```text
ReasonFuse can detect a behavioral regression
without requiring a pre-known exact path.
```

---

# 20. Canary Observation

For candidate runs capture:

```text
release_role = candidate

trajectory state
tool sequence
objective-progress signals
fuse reason
containment latency
```

For stable runs capture the comparable fields.

---

# 21. Rollback / Traffic Removal

Implement a minimal, deterministic rollback action.

Required result:

```text
Candidate removed or weight set to 0
Stable receives 100%
```

Terraform may define steady-state infrastructure.

Operational rollback may be:

```text
APIM config update
script
deployment command
```

depending on what is most reliable in the pinned environment.

Do not build a complex release controller.

---

# 22. Automatic Rollback

Automatic rollback is optional P0.5.

If implemented, keep it simple:

```text
candidate metric threshold exceeded
→ set candidate traffic to 0
```

If not implemented:

```text
manual one-command rollback
```

is sufficient for Phase 4 P0.

Do not delay Phase 4 for full automation.

---

# 23. Core Demo Scenarios

Phase 4 must package four signature scenarios.

## Demo A — OFF / ON

Show:

```text
OFF
→ redundant execution continues

ON
→ ReasonFuse contains it
```

---

## Demo B — Unknown Correct Path

Use a scenario where multiple investigation paths are valid.

Example:

```text
API latency elevated

Possible:
DNS → DB → Deployment
DB → Service → DNS
Deployment → Cache → DB
```

ReasonFuse must judge progress, not path conformity.

---

## Demo C — Outcome Failure

Show:

```text
restart_service
→ approved
→ HTTP 202
→ service still unhealthy
→ POSTCONDITION_FAILED
```

Primary message:

```text
Execution success is not outcome success.
```

---

## Demo D — Candidate Regression

Show:

```text
Candidate cohort
→ repeated no-progress
→ ReasonFuse trips
→ candidate traffic removed
```

---

# 24. Production Narrative

The implementation should support this narrative:

```text
Foundry Guardrails
→ Is the interaction SAFE?

Identity / RBAC / Toolbox
→ Is the action AUTHORIZED?

Agent Framework planning
→ What is the current PLAN?

ReasonFuse
→ Is the trajectory still making OBJECTIVE PROGRESS?

Outcome Verifier
→ Did the real-world action ACTUALLY WORK?
```

Do not blur these responsibilities.

---

# 25. Competition Story Priority

Presentation order:

```text
1. Show behavior
2. Explain ReasonFuse decision
3. Show outcome verification
4. Show benchmark evidence
5. Show candidate regression + rollback
6. Show Microsoft Foundry production architecture
```

Do not start with Terraform or resource inventory.

---

# 26. E2E Demo Script

Create:

```text
demo/run_off_on.sh
demo/run_unknown_path.sh
demo/run_outcome_failure.sh
demo/run_candidate_regression.sh
demo/reset.sh
demo/preflight.sh
```

or equivalent.

Each script should:

```text
reset
preflight
set scenario
run
capture evidence
print PASS/FAIL
```

---

# 27. Demo Evidence

Save:

```text
trace IDs
screenshots
Judge Mode snapshots
APIM affinity evidence
release role
tool sequence
ReasonFuse decision
Outcome Verifier result
rollback confirmation
native Foundry IQ connection and citation proof
pre/post cold-start state and trace lineage
```

Do not store secrets.

---

# 28. APIM Affinity Test Client

Create a small explicit test utility that proves:

```text
one persistent client
→ one backend release across turns
```

Record the affinity cookie/header state.

Also test a fresh client.

---

# 29. SSE Test Client

Create a test utility that records:

```text
chunk content
chunk receive timestamp
final completion timestamp
```

This must prove incremental arrival through APIM.

---

# 30. Production Metrics

Do not invent a giant dashboard.

Expose only useful live metrics:

```text
ReasonFuse trip rate
trip reason
candidate trip rate
healthy completion
postcondition failure
containment latency
release role
```

A small Application Insights query or compact dashboard is enough.

---

# 31. Terraform Scope

Phase 4 Terraform may include:

```text
APIM backend pool
weights
session affinity
policies
monitoring / Application Insights linkage
RBAC required for telemetry and routing
```

Do not expand into:

```text
private endpoints
multi-region
enterprise network topology
WAF architecture
full production HA
```

unless already required by the frozen environment.

---

# 32. Stable/Candidate Version Matrix

Generate a machine-readable matrix.

Example:

```text
Stable:
  agent_version: v17
  toolbox_version: v3
  knowledge_base_version: v5
  model_version: X
  contract_version: rf-v13

Candidate:
  agent_version: v18
  toolbox_version: v3
  knowledge_base_version: v5
  model_version: X
  contract_version: rf-v13
```

This must appear in `PHASE4_REPORT.md`.

---

# 33. Rollback Acceptance

After rollback:

```text
new sessions
→ stable only
```

The verified rollback requirement applies to new sessions: they must route to
Stable after Candidate reaches weight zero. Existing-session behavior is outside
the frozen release scope.

---

# 34. Demo Repeatability

Each signature scenario must be runnable repeatedly after reset.

Minimum target:

```text
3 clean successful executions each
```

before Phase 4 construction is considered ready for independent verification.

Do not count exploratory runs.

---

# 35. PHASE4_REPORT.md

Create:

```text
# Phase 4 Production Story Report

## Environment
...

## Stable / Candidate Matrix
...

## APIM Weighted Canary
Status:
Evidence:

## Session Affinity
Status:
Evidence:

## SSE Through APIM
Status:
Evidence:

## Foundry Tracing / App Insights
Status:
Evidence:

## Native Foundry IQ Retrieval
Status:
Evidence:
Connection / knowledge source:
Knowledge base version:
Query / citation proof:

## Forced Cold-Start Recovery
Status:
Evidence:
Restart mechanism:
Pre-restart state:
Post-restart state:
History / trace continuity:

## Judge Mode
Status:
Evidence:

## Demo A — OFF / ON
Status:
Evidence:

## Demo B — Unknown Correct Path
Status:
Evidence:

## Demo C — Outcome Failure
Status:
Evidence:

## Demo D — Candidate Regression
Status:
Evidence:

## Rollback
Status:
Evidence:

## Architecture Change Required?
YES / NO

## Phase 4 Result
PASS / BLOCKED
```

---

# 36. What Phase 4 Must NOT Do

Do not spend Phase 4 on:

```text
new detectors
new benchmark categories
new agent framework
new database
multi-agent system
advanced governance
AI Red Teaming
large usability study
final video editing
submission packaging
```

Those are outside the phase.

---

# 37. Construction Completion Criteria

Construction is complete only when:

```text
[ ] Stable and Candidate releases exist

[ ] release lineage is recorded

[ ] Stable/Candidate use same Toolbox version

[ ] Stable/Candidate use same KB version

[ ] APIM 95/5 pool configured

[ ] session affinity configured

[ ] persistent client preserves affinity

[ ] fresh client can receive independent routing

[ ] SSE arrives incrementally through APIM

[ ] OTel / Foundry Tracing / App Insights path works

[ ] native Foundry IQ connection and knowledge source exist

[ ] native retrieval returns source/citation evidence with a pinned version

[ ] native retrieval evidence is distinct from `retrieval_fixture`

[ ] bounded platform cold-start/restart procedure exists

[ ] post-cold-start conversation history and ReasonFuse state are restored

[ ] pre/post cold-start trace and session lineage is captured

[ ] Judge Mode uses real runtime data

[ ] OFF/ON demo works

[ ] Unknown Correct Path demo works

[ ] Outcome Failure demo works

[ ] Candidate Regression demo works

[ ] rollback command/path exists

[ ] rollback can set Candidate traffic to zero

[ ] demo scripts exist

[ ] evidence capture exists

[ ] PHASE4_REPORT.md template exists
```

At the end, state only:

```text
PHASE 4 CONSTRUCTION COMPLETE
READY FOR INDEPENDENT VALIDATION
```

Do not self-award Phase 4 PASS.
