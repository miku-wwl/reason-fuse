# ReasonFuse Phase 6 — Microsoft Agent-a-thon Submission Construction Plan

> **Phase:** 6  
> **Target:** Microsoft Agent-a-thon submission version  
> **Status at entry:** Phase 1–5 completed; ReasonFuse v5.0.0 architecture/core freeze already established  
> **Primary principle:** **Do not redesign the ReasonFuse core. Phase 6 is submission hardening, Azure E2E closure, evidence, packaging, and presentation.**  
> **Phase 7:** Reserved for the 1010 / Singapore competition version and formal ≥6 Skill packaging.

---

# 0. Phase 6 Mission

Phase 6 turns the already-frozen ReasonFuse implementation into the **strongest Microsoft Agent-a-thon submission package**.

The goal is not:

```text
add more architecture
add more agents
rewrite the deterministic core
turn ReasonFuse into a different product
```

The goal is:

```text
prove the existing architecture in Azure
close the important cloud-E2E evidence gaps
package the existing core as clear reliability capabilities
produce measurable OFF vs ON evidence
improve business clarity
record a strong 3-minute competition presentation
submit a repository whose claims exactly match its evidence
```

Phase 6 should end with:

> **A judge can understand the problem in seconds, see the ReasonFuse intervention in a real Foundry path, inspect deterministic evidence, and verify that the project is more than a local prototype.**

---

# 1. Phase 6 Entry Baseline

The current repository already contains the important ReasonFuse runtime core:

```text
Foundry Hosted Agent entry path
Responses 2.0.0 hosting
history_source="agent_server"
store=False
AgentSession-backed ReasonFuse state
deterministic progress engine
Todo != objective progress
Exact Loop detection
Oscillation detection
Retrieval Churn detection
Useful Recheck handling
bounded Run Contract
native approval configuration
postcondition / Outcome Verification
ReasonFuse Function Middleware
structured telemetry
APIM 95/5 + session-affinity IaC
15-scenario local validation specification
unit / boundary tests
dependency pinning
```

The current submission gaps are mostly **evidence and demo gaps**, not core-architecture gaps.

Known Phase 6 closure targets:

```text
Cloud approval path              NOT YET PROVEN E2E
Cloud outcome verification       NOT YET PROVEN E2E
Operations demo path             NOT SELF-CONTAINED IN CURRENT REPO
Application Insights evidence    NOT YET CAPTURED AS FINAL SUBMISSION PROOF
Toolbox / IQ live proof          OPTIONAL / NOT YET FINALIZED
APIM live canary proof           OPTIONAL POLISH
Final architecture diagram       PENDING
Final 3-minute presentation      PENDING
OFF vs ON comparative evidence   PENDING
```

---

# 2. Phase 6 Freeze Rules

## 2.1 Core stays frozen

The following directories/components are considered **frozen by default**:

```text
src/reasonfuse/core/
    contract.py
    detectors.py
    engine.py
    fingerprint.py
    middleware.py
    outcome.py
    progress.py
    provider.py
    state.py
```

Changes are allowed only when:

```text
an actual Phase 6 Azure E2E run exposes
a concrete correctness or integration blocker
```

If a change is required:

1. identify the blocker;
2. make the smallest possible fix;
3. rerun all existing local tests;
4. rerun affected 15-scenario cases;
5. rerun the relevant Azure E2E signature case;
6. document why the core freeze had to be touched.

No speculative refactor.

---

## 2.2 No six-Agent rewrite

Phase 6 must **not** transform the six ReasonFuse capabilities into six LLM agents.

Wrong:

```text
Progress Agent
Loop Agent
Approval Agent
Verification Agent
...
```

Correct:

```text
Agent / Agent System
        ↓
ReasonFuse deterministic control plane
        ↓
six reliability capabilities
        ↓
Tools / real world
```

ReasonFuse's differentiator remains:

> **Critical control decisions come from deterministic runtime state and evidence accounting, not another LLM judging the LLM.**

---

## 2.3 No premature Phase 7 packaging

Phase 6 may name and present the six capabilities, but should not yet build the full 1010 packaging requirements such as:

```text
six separate SKILL.md packages
20+ tests per Skill
1010 trigger-hit evaluation
1010 installable Skill bundle
SP-A-specific multi-agent orchestration package
```

Those belong to **Phase 7**.

Phase 6 only ensures the capability boundaries are clear enough that Phase 7 can package them later.

---

# 3. Phase 6 Submission Architecture

The Microsoft submission should present ReasonFuse as:

> **The reliability layer for autonomous AI agents.**

Primary competition architecture:

```text
User / Incident Goal
        ↓
Microsoft Foundry Hosted Agent
        ↓
Microsoft Agent Framework
        ↓
ReasonFuse Function Middleware
        ↓
┌──────────────────────────────────────────────┐
│      ReasonFuse Reliability Control Plane    │
│                                              │
│  1. Trajectory Guard                        │
│  2. Progress Accounting                     │
│  3. Failure Detection                       │
│  4. Execution Contract                      │
│  5. Approval Control                        │
│  6. Outcome Verification                    │
│                                              │
│  Cross-cutting: Observability / Telemetry   │
└──────────────────────────────────────────────┘
        ↓
Foundry Toolbox / Foundry IQ / Operations
        ↓
Real-world state
        ↓
Fresh verification
```

Important:

> These are **six capabilities of one deterministic runtime**, not six independently reasoning agents.

---

# 4. Six Reliability Capabilities

These capability names become stable Phase 6 presentation terminology and should remain compatible with Phase 7.

## Capability 1 — Trajectory Guard

Maps to existing:

```text
Pre-call interception
tool fingerprinting
current containment state
ALLOW / BLOCK decision
```

Business meaning:

> Prevent an already-invalid execution trajectory from continuing to dispatch real tools.

---

## Capability 2 — Progress Accounting

Maps to existing:

```text
Evidence Delta
World-State Delta
Retrieval Delta
Todo Delta
Postcondition Delta
Objective Progress
```

Business meaning:

> Separate “the agent did something” from “the agent actually moved the objective forward.”

Key competition line:

> **Planning changed. Reality did not.**

---

## Capability 3 — Failure Detection

Maps to existing:

```text
Exact Loop
Oscillation
Retrieval Churn
generic no-progress handling
Useful Recheck preservation
```

Business meaning:

> Detect repeated or unproductive execution patterns without asking another LLM to judge the trajectory.

---

## Capability 4 — Execution Contract

Maps to existing:

```text
max steps
max tool calls
max stalled steps
oscillation / churn budgets
side-effect budgets
verification reservation
```

Business meaning:

> Put a deterministic bound around autonomous execution and cost/risk exposure.

---

## Capability 5 — Approval Control

Maps to existing:

```text
Microsoft Agent Framework native tool approval
restart_service approval requirement
approval response integration
side-effect flow
```

Business meaning:

> Keep humans in control of high-impact actions without rebuilding a proprietary approval system.

---

## Capability 6 — Outcome Verification

Maps to existing:

```text
pending postcondition
accepted side effect != success
fresh verification read
OutcomeVerifier
OUTCOME_VERIFIED
POSTCONDITION_FAILED
OUTCOME_UNKNOWN
```

Business meaning:

> Prevent the agent from falsely declaring success just because a side-effect API returned accepted / HTTP 202.

---

## Cross-cutting — Observability

Maps to existing:

```text
OTel attributes
ReasonFuse structured events
Application Insights
trajectory_state
progress_state
failure_type
fuse_reason
contract_version
delta signals
```

Business meaning:

> Make autonomous-agent control decisions inspectable and auditable.

---

# 5. Phase 6 Workstreams

Phase 6 is divided into six workstreams.

```text
6A  Baseline Lock
6B  Azure E2E Closure
6C  Comparative Evidence
6D  Competition Architecture & Capability Packaging
6E  Business Clarity + 3-Minute Presentation
6F  Final Submission Audit
```

---

# 6A. Baseline Lock

## Objective

Create a clean, reproducible Phase 6 starting point before cloud work begins.

## Tasks

```text
[ ] Confirm current main branch / submission branch commit
[ ] Run unit/boundary tests
[ ] Run local_wiring.py
[ ] Run local_history_audit.py
[ ] Run compileall
[ ] Run git diff --check
[ ] Validate Terraform format / syntax / safe plan
[ ] Execute the 15 local scenarios once
[ ] Save a Phase 6 baseline validation result
```

## Expected result

```text
Core tests                PASS
Local wiring              PASS
History ownership         PASS
15 scenarios              PASS or explicitly documented
Terraform static checks   PASS
No uncommitted mystery    PASS
```

If the baseline is not clean, Phase 6 Azure work does not begin.

---

# 6B. Azure E2E Closure

This is the most important engineering workstream in Phase 6.

## 6B.1 Goal

Close the gap between:

```text
LOCALLY IMPLEMENTED
```

and:

```text
LIVE MICROSOFT E2E PROVEN
```

for the strongest ReasonFuse claims.

---

## 6B.2 Operations Demo Boundary

The current repository provisions an Operations Web App but does not contain the matching self-contained service source.

Phase 6 should restore the **smallest deterministic Operations demo surface required for E2E**.

Required operations:

```text
dns_resolution
service_status
database_health
restart_service
retrieval_fixture
```

Properties:

```text
deterministic
resettable
demo-safe
no production credentials
no real infrastructure mutation
clear accepted / observed-state separation
supports healthy / unhealthy / stale verification states
```

The purpose is **not** to build another backend product.

Its only job is to make the ReasonFuse cloud demo:

```text
self-contained
repeatable
truthful
cheap
```

### Required side-effect semantics

`restart_service` should support:

```text
request accepted
        ↓
world state transitions
        ↓
fresh service_status read
        ↓
OutcomeVerifier determines result
```

The operation response must not itself prove recovery.

---

## 6B.3 Live Signature Runs

Phase 6 should capture a **small curated set**, not a large benchmark.

### LIVE-1 — Hosted Runtime + State

Prove:

```text
Foundry Hosted Agent is running
Responses 2.0.0 path is real
history_source="agent_server"
store=False
ReasonFuse middleware executes
AgentSession state survives the runtime flow
```

Pass evidence:

```text
Hosted request/response
ReasonFuse state fields
trace / structured event
```

---

### LIVE-2 — Deterministic Containment

Use one visually obvious failure trajectory.

Preferred:

```text
service_status
database_health
service_status
database_health
...
```

or a clear repeated equivalent action.

Prove:

```text
objective progress stalls
        ↓
ReasonFuse detects invalid trajectory
        ↓
containment occurs
        ↓
next operational dispatch is blocked
        ↓
telemetry explains why
```

Required evidence:

```text
tool trajectory
containment decision
failure / fuse reason
step / contract state
Application Insights event if available
```

---

### LIVE-3 — Native Approval + Verified Outcome

This is Phase 6 P0.

Flow:

```text
Agent proposes restart_service
        ↓
Microsoft native approval generated
        ↓
Tool does NOT execute before approval
        ↓
Approval granted
        ↓
restart_service returns accepted
        ↓
ReasonFuse does NOT call this success
        ↓
pending postcondition persists
        ↓
fresh service_status
        ↓
OutcomeVerifier
        ↓
OUTCOME_VERIFIED
```

Also capture one failure/unknown variant if cheap:

```text
accepted restart
        ↓
fresh status still unhealthy / stale
        ↓
POSTCONDITION_FAILED or OUTCOME_UNKNOWN
```

This proves one of ReasonFuse's strongest claims:

> **Accepted is not verified.**

---

### LIVE-4 — Application Insights / OTel

Capture at least:

```text
REASONFUSE_OBSERVATION
REASONFUSE_FUSE_TRIPPED
```

and important attributes such as:

```text
trajectory_state
progress_state
objective/evidence/world/retrieval/postcondition signals
failure_type
fuse_reason
contract_version
```

Pass condition:

> A judge-facing screenshot or trace can show why ReasonFuse made the decision.

---

### LIVE-5 — Toolbox / Foundry IQ

P0 only if it is easy and stable inside the event environment.

One genuine integration is enough.

Prove:

```text
Foundry Agent
    ↓
Toolbox or Foundry IQ
    ↓
real Microsoft integration
    ↓
ReasonFuse observes normalized result
```

Do not spend hours making optional retrieval infrastructure overshadow the core submission.

---

### LIVE-6 — APIM Sticky Canary

**P0.5 only.**

If stable and inexpensive, prove:

```text
95 Stable / 5 Candidate
session affinity
SSE pass-through
```

If this threatens submission stability or time budget:

```text
keep IaC
show architecture
do not make live APIM proof a submission blocker
```

---

# 6C. Comparative Evidence — OFF vs ON

Phase 6 should add a **small controlled comparison**, not a production benchmark.

## Goal

Convert ReasonFuse from:

```text
interesting architecture
```

into:

```text
measurably useful reliability layer
```

---

## 6C.1 Required comparison scenarios

Use 2–3 signature scenarios.

### Scenario A — Repeated / Oscillating Diagnostics

Compare:

```text
ReasonFuse OFF
vs
ReasonFuse ON
```

Measure:

```text
total tool calls
redundant tool calls
containment step
time until bounded stop
final result
```

---

### Scenario B — Side Effect + Verification

Compare conceptual behavior:

```text
Without verification:
restart accepted → agent may declare success

With ReasonFuse:
restart accepted
→ pending postcondition
→ fresh status
→ verified / failed / unknown
```

Measure:

```text
false success prevented
verification reads
final verified outcome
```

---

### Scenario C — Optional Retrieval Churn

If demo time permits:

```text
different queries
→ same normalized evidence
→ ReasonFuse identifies retrieval churn
```

Measure:

```text
retrieval calls
new evidence count
contained / not contained
```

---

## 6C.2 Metrics

Preferred judge-facing metrics:

```text
Tool Calls
Redundant Calls
Unsafe / High-impact Actions
Containment Step
Verified Outcome
Time to Verified Outcome
```

Optional:

```text
model/tool cost estimate
```

Only use cost if it can be calculated honestly from known call counts/rates.

Do not invent customer savings.

---

## 6C.3 Evidence Output

Create one concise final artifact:

```text
ReasonFuse_PHASE6_COMPARATIVE_EVIDENCE.md
```

It should contain:

```text
scenario
environment
OFF trajectory
ON trajectory
metrics
result
limitations
```

No huge evaluator framework.

---

# 6D. Competition Architecture & Capability Packaging

## Goal

Make the ReasonFuse system understandable in under 20 seconds.

This workstream is primarily documentation / demo packaging.

---

## 6D.1 Architecture Diagram

Final diagram must visually separate:

```text
Microsoft platform capabilities
vs
ReasonFuse capabilities
vs
demo Operations world
```

Required Microsoft components:

```text
Foundry Hosted Agent
Agent Framework
native Approval
Foundry Toolbox / IQ when actually used
Application Insights
APIM only if retained in final story
```

Required ReasonFuse components:

```text
Trajectory Guard
Progress Accounting
Failure Detection
Execution Contract
Approval Control integration
Outcome Verification
Observability
```

---

## 6D.2 Capability Status View

A tiny judge-facing status display is allowed.

Example:

```text
ReasonFuse Reliability Control Plane

Trajectory Guard        ACTIVE
Progress Accounting     STALLED
Failure Detection       OSCILLATION
Execution Contract      7 / 12
Approval Control        REQUIRED
Outcome Verification    PENDING
```

This can be:

```text
terminal output
static HTML
video overlay
structured log rendering
```

Do not build a large dashboard.

---

## 6D.3 Phase 7 Compatibility

The six names should remain stable:

```text
trajectory_guard
progress_accounting
failure_detection
execution_contract
approval_control
outcome_verification
```

Phase 7 can later turn each into:

```text
SKILL.md
supporting scripts
self-tests
trigger/input/output schema
```

Phase 6 does **not** need to do that packaging yet.

---

# 6E. Business Clarity + 3-Minute Presentation

## 6E.1 Competition Positioning

Primary:

> **ReasonFuse — The Reliability Layer for Autonomous AI Agents**

Problem statement:

> Companies are beginning to let AI agents inspect production systems and take operational actions. But an agent can loop, waste calls, take risky actions, or declare recovery even when the service is still unhealthy.

Core technical sentence:

> **Foundry runs the agent. ReasonFuse decides whether the run is still making progress.**

Outcome sentence:

> **Agents can take actions. ReasonFuse makes sure those actions remain productive, bounded, and verified.**

---

## 6E.2 Fixed Buyer / User

Competition story should focus on:

```text
Platform Engineering
SRE
AI Platform
Enterprise Agent Governance
```

Primary persona:

> **A Platform/SRE team introducing autonomous agents into production operations.**

---

## 6E.3 Main Demo Scenario

Use one scenario throughout:

```text
Production checkout/payment service degraded
        ↓
Agent receives:
"Restore service health safely."
```

Do not switch industries during the three-minute presentation.

---

## 6E.4 Three-Minute Structure

### 0:00–0:25 — Problem

Show:

```text
autonomous agent
real production tools
loop / risky action / false recovery risk
```

No architecture yet.

---

### 0:25–0:55 — Without ReasonFuse

Show a short failure trajectory.

Example:

```text
get_logs
get_metrics
get_logs
get_metrics
restart
status
...
```

Judge-facing result:

```text
too many calls
redundant work
service still unhealthy
FALSE RECOVERY
```

---

### 0:55–2:05 — With ReasonFuse

Show only the most powerful moments:

```text
1. no-progress / oscillation detected
2. execution contained
3. risky restart requires native approval
4. accepted restart is NOT success
5. fresh verification
6. OUTCOME_VERIFIED
```

---

### 2:05–2:35 — Before / After

Display one simple table:

| Metric | Without ReasonFuse | With ReasonFuse |
|---|---:|---:|
| Tool calls | measured | measured |
| Redundant calls | measured | measured |
| Unsafe actions | measured | measured |
| Time to verified result | measured | measured |
| Verified recovery | No / unclear | Yes |

Use actual Phase 6 evidence.

---

### 2:35–3:00 — Technical Moat + Close

Explain:

```text
not another LLM judge

deterministic runtime state
objective progress
loop / oscillation / churn detection
bounded execution
native approval integration
postcondition verification
```

Final line:

> **ReasonFuse is the reliability layer between autonomous agents and real-world production actions.**

---

# 6F. Final Submission Audit

No submission until all P0 gates are checked.

---

## 6F.1 P0 Gates

### Repository

```text
[ ] Unit / boundary PASS
[ ] local_wiring PASS
[ ] local_history_audit PASS
[ ] compileall PASS
[ ] git diff --check PASS
[ ] Terraform static checks PASS
[ ] README truthful and current
[ ] no secrets / local Azure state committed
```

### Core Behavior

```text
[ ] 15 lightweight scenarios executed once
[ ] healthy scenario PASS
[ ] no-progress PASS
[ ] Exact Loop PASS
[ ] Oscillation PASS
[ ] Retrieval Churn PASS
[ ] Outcome Verified PASS
[ ] Postcondition Failed / Unknown PASS
```

### Microsoft E2E

```text
[ ] Hosted Agent live proof
[ ] middleware live proof
[ ] deterministic containment live proof
[ ] native approval live proof
[ ] accepted != success live proof
[ ] fresh outcome verification live proof
[ ] Application Insights / telemetry proof
```

### Competition Evidence

```text
[ ] OFF vs ON comparison
[ ] measured metrics
[ ] final architecture diagram
[ ] six reliability capabilities clearly labeled
[ ] Microsoft vs ReasonFuse boundary clear
```

### Presentation

```text
[ ] 3-minute script finalized
[ ] demo fits time limit
[ ] no unsupported production claims
[ ] no fake customer ROI
[ ] captions / zoom / text readable
[ ] final video recorded
[ ] submission links verified
```

---

## 6F.2 P0.5 — Only If Time Remains

```text
[ ] Foundry IQ live screenshot
[ ] Toolbox trace
[ ] APIM sticky-canary proof
[ ] small judge status HTML
[ ] second incident scenario
[ ] polished animated architecture transitions
```

None of these can block P0 submission.

---

# 7. Proposed Repository Changes

Phase 6 should stay additive and small.

## Likely P0 additions

```text
ReasonFuse_PHASE6_MICROSOFT_SUBMISSION_EVIDENCE.md
docs/
    phase6/
        architecture.md
        demo-script.md

<minimal Operations demo source>
    deterministic demo tool endpoints
    resettable world-state fixture
```

Exact Operations source location should be chosen to fit the final deployment path; do not create duplicate deployment systems.

## Likely updates

```text
README.md
azure.yaml                      only if deployment closure requires it
infra/operations.tf             only if Operations deployment wiring requires it
agent.py                        only for verified event-environment integration
telemetry configuration         only if live export reveals a blocker
```

## Core files

```text
src/reasonfuse/core/*
```

Expected change:

```text
NONE
```

unless Azure E2E exposes a real core blocker.

---

# 8. Phase 6 Development Order

Do not work in arbitrary order.

```text
6A Baseline Lock
        ↓
6B Operations + Azure E2E
        ↓
6B LIVE-3 Approval + Outcome
        ↓
6B Telemetry Evidence
        ↓
6C OFF vs ON Measurement
        ↓
6D Architecture / Capability Packaging
        ↓
6E Business Story / 3-Minute Demo
        ↓
6F Final Audit
        ↓
SUBMIT
```

Key rule:

> **Engineering proof before presentation polish.**

---

# 9. Suggested Calendar

Assuming the Microsoft Agent-a-thon window is **17 Sep – 24 Sep**:

## Before 17 Sep

```text
Finish ReasonFuse learning
Review Phase 6 plan
Prepare Azure credentials / quota / budget
Confirm local baseline
Do not destabilize core
```

## 17–19 Sep

```text
Phase 6A
Phase 6B
Operations demo closure
Hosted Agent deployment
Approval + Outcome E2E
```

## 20–21 Sep

```text
Telemetry proof
Containment proof
OFF vs ON comparison
Fix only verified blockers
```

## 22 Sep

```text
Final architecture
Six reliability capability presentation
README competition narrative
Business clarity
```

## 23 Sep

```text
Record / edit 3-minute presentation
Final screenshots / evidence
Dry run
```

## 24 Sep

```text
Final repository audit
Replay critical demo once
Check links
Submit
Do not introduce new features
```

---

# 10. Failure Policy During Phase 6

If Azure E2E fails:

```text
classify failure first
```

Possible classes:

```text
A. environment / quota / permission
B. deployment wiring
C. Microsoft SDK/API mismatch
D. demo Operations integration
E. telemetry/export
F. actual ReasonFuse core correctness defect
```

Only class **F** justifies changing the frozen core.

For A–E:

> Fix the boundary, not the algorithm.

---

# 11. Cost-Control Policy

Phase 6 remains hackathon-grade, not production certification.

Do not create:

```text
hundreds of model runs
large performance benchmark
production load test
24/7 Azure resources
large dashboard
new database
Kubernetes
service mesh
multi-region architecture
```

Use:

```text
local tests first
small curated cloud runs
capture evidence once
tear down resources when no longer needed
```

---

# 12. Phase 6 Completion Definition

Phase 6 is complete only when all of the following are true:

```text
1. Existing deterministic core still passes local validation.

2. A real Microsoft Foundry Hosted Agent path is captured.

3. A live ReasonFuse containment decision is demonstrated.

4. A native high-impact approval flow is demonstrated.

5. An accepted side effect is followed by fresh verification.

6. OUTCOME_VERIFIED / FAILED / UNKNOWN semantics are truthfully demonstrated.

7. Application Insights / OTel provides inspectable ReasonFuse evidence.

8. At least one OFF vs ON comparison provides measured evidence.

9. The six Reliability Capabilities are understandable without refactoring the core.

10. Microsoft platform capability and ReasonFuse capability are clearly separated.

11. The final 3-minute presentation explains:
    customer → problem → failure → ReasonFuse → evidence → value.

12. Final repository claims match actual proof.

13. No Phase 7 competition packaging has destabilized Phase 6.

14. Submission is delivered before the Microsoft deadline.
```

---

# 13. Phase 6 → Phase 7 Handoff

Phase 6 must leave Phase 7 a clean foundation.

Stable handoff concepts:

```text
Trajectory Guard
Progress Accounting
Failure Detection
Execution Contract
Approval Control
Outcome Verification
Observability
```

Phase 7 will then add the 1010-specific layer:

```text
≥6 formal Skills
SKILL.md per Skill
supporting scripts
≥20 tests per Skill
trigger system
shared schema
multi-agent / SP-A competition scenario
installable package
1010-specific E2E
1010 presentation
```

Phase 7 should reuse Phase 6 evidence and capability boundaries wherever possible.

---

# 14. Final Phase 6 Rule

> **Do not make ReasonFuse larger just to make the submission look larger.**

Phase 6 wins by making the existing project:

```text
real in Azure
measurable
understandable
credible
visually clear
easy to judge
```

The core competitive thesis remains:

> **Foundry runs the agent. ReasonFuse decides whether the run is still making progress — and verifies that real-world success actually happened.**
