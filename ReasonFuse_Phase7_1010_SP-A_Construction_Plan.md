# ReasonFuse Phase 7 — 1010 Track B / SP-A Competition Construction Plan

> **Phase:** 7  
> **Target:** 1010 Digital Human Festival / Global AI Agent Competition — Track B  
> **Recommended direction:** **SP-A — Collaborative Orchestration Hub Skill Package**  
> **Entry condition:** Phase 1–5 complete; Phase 6 Microsoft Agent-a-thon version completed or frozen for submission  
> **Primary principle:** **Reuse the same ReasonFuse core IP. Build a competition adapter, formal Skill packages, multi-agent orchestration, self-tests, trigger evaluation, and one complete SP-A scenario around it.**  
> **Core rule:** Do not turn ReasonFuse into six LLM judges. The six competition Skills remain deterministic reliability/control capabilities unless a Skill genuinely requires agentic orchestration.

---

# 0. Phase 7 Mission

Phase 7 turns ReasonFuse from a Microsoft-focused runtime reliability submission into a **Track B Skill-package competition entry**.

The source requirements for Track B include:

```text
≥6 effective Skills
one unified scenario
installable / testable / demoable end-to-end closed loop
clear Skill structure
verifiable supporting materials
real-world business scenario
```

For SP-A specifically, the competition asks for a collaborative orchestration hub that can:

```text
understand / decompose tasks
design long-horizon plans
dispatch and coordinate multiple role agents
support adversarial gameplay simulation
support collaborative stress testing / fault injection
support runtime visualization and monitoring
```

The SP-A demo pipeline is:

```text
Intent Input
    ↓
Task Decomposition / Planning
    ↓
Multi-Agent Division of Labor & Collaboration
    ↓
Result Completion
    ↓
Monitoring
```

Each Skill is expected to include:

```text
SKILL.md
supporting scripts
≥20 self-test cases
```

The global Track B acceptance criteria also require:

```text
Skill Count            ≥6 effective Skills
Self-test Coverage     100% pass rate
Trigger Hit Rate       ≥90%
Main Pipeline          ≥1 end-to-end demoable pipeline
Delivery Format        installable / packagable
```

Phase 7 therefore is not merely “rename six modules.”

It must produce a **real competition distribution**.

---

# 1. Phase 7 Product Positioning

Phase 6 positioning:

> **ReasonFuse — The Reliability Layer for Autonomous AI Agents**

Phase 7 extends this into a collaborative orchestration story:

> **ReasonFuse — A Reliability Control Plane for Multi-Agent Collaboration**

Competition-facing problem:

> Multi-agent systems can decompose work and collaborate, but collaboration itself can fail: agents repeat work, oscillate between plans, retrieve the same evidence, exceed execution budgets, perform high-impact actions, or declare success without proving that the real-world outcome happened.

Phase 7 solution:

```text
Multi-Agent Orchestrator
        ↓
ReasonFuse Reliability Skills
        ↓
Deterministic progress control
        ↓
Failure detection
        ↓
Bounded execution
        ↓
Approval
        ↓
Outcome verification
        ↓
Observable, verified completion
```

---

# 2. Phase 7 Boundary: What Changes vs What Stays Frozen

## 2.1 Frozen Core

Keep the ReasonFuse v5.0.0 deterministic core frozen by default:

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

Core changes are allowed only if Phase 7 integration reveals a concrete correctness blocker.

Do not rewrite the core merely to match competition terminology.

---

## 2.2 Phase 7 Adds

Phase 7 may add:

```text
competition/
    phase7/
        skills/
        orchestration/
        scenarios/
        tests/
        evaluation/
        packaging/
        demo/
```

or an equivalent clean structure.

The exact directory names may be adapted to the current repository, but the separation must stay clear:

```text
ReasonFuse Core
    ≠
1010 Competition Packaging
```

---

# 3. Recommended Track: SP-A

SP-A is the strongest fit because ReasonFuse already has:

```text
runtime control
progress accounting
failure detection
bounded execution
approval integration
outcome verification
fault injection mindset
telemetry / observability
```

SP-A adds the missing upper layer:

```text
intent decomposition
long-horizon planning
multi-agent role assignment
agent-to-agent coordination
collaborative stress testing
runtime visualization
```

This produces a clean stack:

```text
User Goal
    ↓
Collaborative Orchestration Hub
    ↓
Planner / Diagnosis / Operations / Verifier Agents
    ↓
ReasonFuse Reliability Control Plane
    ↓
Tools / Simulated World
    ↓
Verified Outcome
```

---

# 4. Phase 7 Competition Scenario

Use one unified scenario for all Skills.

Recommended scenario:

> **Multi-Agent Production Incident Recovery**

Example incident:

```text
Checkout / payment service degraded
```

User intent:

```text
Restore service health safely,
identify the failure,
coordinate diagnosis and remediation,
and verify the real-world outcome.
```

Role agents:

```text
Incident Commander
Diagnosis Agent
Operations Agent
Verification Agent
```

Optional fifth role:

```text
Knowledge / Evidence Agent
```

Do not add agents merely to increase count.

Every role must have a distinct responsibility.

---

# 5. Main SP-A Pipeline

The competition pipeline should map naturally to the official SP-A flow.

```text
Intent Input
"Restore checkout health safely"
        ↓
Task Decomposition
        ↓
Long-Horizon Plan
        ↓
Lead / Role Assignment
        ↓
Multi-Agent Collaboration
        ↓
Tool Proposals
        ↓
ReasonFuse Reliability Skills
        ↓
Tool Execution / World-State Change
        ↓
Fresh Verification
        ↓
Result Completion
        ↓
Runtime Monitoring / Evidence
```

The judge should be able to see:

```text
who planned
who acted
what ReasonFuse blocked
what required approval
what changed in the world
how success was verified
```

---

# 6. The Six Formal Phase 7 Skills

Phase 7 turns the six Phase 6 capability names into formal competition Skills.

Use stable names so both competitions share the same conceptual model.

---

## Skill 1 — Trajectory Guard

### Purpose

Prevent an invalid or already-contained execution trajectory from dispatching another action.

### Existing ReasonFuse basis

```text
pre-call interception
tool fingerprint
containment state
ALLOW / BLOCK decision
```

### Competition trigger examples

```text
guard this proposed action
check whether this action may execute
validate trajectory before dispatch
```

### Input

```text
current runtime state
proposed tool/action
current run contract
recent trajectory
```

### Output

```text
ALLOW
BLOCK
reason
fingerprint
```

### Required supporting material

```text
SKILL.md
adapter / callable wrapper
20+ self-tests
trigger test set
example invocation
```

---

## Skill 2 — Progress Accounting

### Purpose

Determine whether the system is making meaningful objective progress.

### Existing ReasonFuse basis

```text
Evidence Delta
World-State Delta
Retrieval Delta
Todo Delta
Postcondition Delta
Objective Progress
```

### Competition trigger examples

```text
measure objective progress
evaluate whether this step advanced the goal
compare world/evidence delta
```

### Input

```text
before state
after observation
objective / todo state
retrieval identity
postcondition state
```

### Output

```text
progress_state
delta signals
stalled / advancing
```

---

## Skill 3 — Failure Detection

### Purpose

Identify deterministic failure patterns.

### Existing ReasonFuse basis

```text
Exact Loop
Oscillation
Retrieval Churn
No Progress
Useful Recheck preservation
```

### Competition trigger examples

```text
detect collaboration failure
detect loop or oscillation
check for retrieval churn
```

### Input

```text
trajectory
fingerprints
progress history
retrieval identities
```

### Output

```text
failure_type
detector result
recommended containment decision
```

---

## Skill 4 — Execution Contract

### Purpose

Bound autonomous execution.

### Existing ReasonFuse basis

```text
max_steps
max_tool_calls
max_stalled_steps
max_oscillation_cycles
max_retrieval_churn
max_side_effects
verification reserve
```

### Competition trigger examples

```text
check execution budget
validate run contract
check remaining tool budget
```

### Input

```text
current counters
contract version
proposed action class
```

### Output

```text
budget status
remaining allowance
ALLOW / BLOCK / verification reserved
```

---

## Skill 5 — Approval Control

### Purpose

Gate high-impact side effects using native/platform approval.

### Existing ReasonFuse basis

```text
approval-required tool classification
approval response integration
side-effect execution control
```

### Competition trigger examples

```text
request approval
gate risky operation
require human confirmation
```

### Input

```text
proposed side effect
risk class
approval state
```

### Output

```text
APPROVAL_REQUIRED
APPROVED
DENIED
NOT_REQUIRED
```

### Important

Do not build a fake proprietary approval engine merely for the competition.

Keep the principle:

> **Use platform-native primitives where they already exist.**

---

## Skill 6 — Outcome Verification

### Purpose

Verify that a side effect actually produced the intended real-world result.

### Existing ReasonFuse basis

```text
pending postcondition
fresh verification read
resource identity / generation checks
OutcomeVerifier
OUTCOME_VERIFIED
POSTCONDITION_FAILED
OUTCOME_UNKNOWN
```

### Competition trigger examples

```text
verify the outcome
check postcondition
confirm recovery
```

### Input

```text
pending postcondition
fresh observation
resource identity
generation / freshness
```

### Output

```text
OUTCOME_VERIFIED
POSTCONDITION_FAILED
OUTCOME_UNKNOWN
evidence
```

---

# 7. Cross-Cutting Capability — Observability

Observability should not be counted as one of the minimum six unless needed.

It should support all six Skills.

Show:

```text
trajectory state
progress state
failure type
fuse reason
contract usage
approval state
postcondition state
agent role
task / subtask id
```

Phase 7 must add collaboration-aware identifiers:

```text
collaboration_id
task_id
subtask_id
agent_role
handoff_from
handoff_to
```

Do not put private chain-of-thought into telemetry.

---

# 8. Skill Package Standard

Each Skill folder should follow one consistent contract.

Recommended structure:

```text
competition/phase7/skills/
    trajectory_guard/
        SKILL.md
        skill.py
        schema.json
        examples/
        tests/

    progress_accounting/
        SKILL.md
        skill.py
        schema.json
        examples/
        tests/

    failure_detection/
        SKILL.md
        skill.py
        schema.json
        examples/
        tests/

    execution_contract/
        SKILL.md
        skill.py
        schema.json
        examples/
        tests/

    approval_control/
        SKILL.md
        skill.py
        schema.json
        examples/
        tests/

    outcome_verification/
        SKILL.md
        skill.py
        schema.json
        examples/
        tests/
```

Exact filenames may be adjusted to the organizer's final template.

Do not assume the organizer requires this exact filesystem shape unless their final submission template confirms it.

---

# 9. SKILL.md Standard

Every `SKILL.md` should use the same sections:

```text
# Skill Name

## Purpose
## When to Trigger
## When NOT to Trigger
## Inputs
## Outputs
## Preconditions
## Deterministic Logic
## Failure Modes
## Example
## Self-Test Coverage
## Integration in the Main Scenario
## Dependencies
## Limitations
```

Especially include:

```text
When NOT to Trigger
```

because a high trigger hit rate is not enough if Skills fire on irrelevant requests.

---

# 10. Trigger System

The Track B acceptance criteria require:

```text
Trigger Hit Rate ≥90%
```

Phase 7 therefore needs an explicit trigger evaluation layer.

Recommended design:

```text
User / Orchestrator Intent
        ↓
Trigger Router
        ↓
Skill selection
```

The trigger system must distinguish:

```text
Trajectory Guard
Progress Accounting
Failure Detection
Execution Contract
Approval Control
Outcome Verification
```

from irrelevant requests.

Do not rely on vague Skill names alone.

---

# 11. Trigger Evaluation Dataset

Build a small but meaningful dataset.

Recommended minimum:

```text
positive triggers per Skill      20+
negative / confusing examples   20+
cross-Skill ambiguity cases     20+
```

The organizer only states a ≥90% trigger hit rate; it does not specify the exact evaluation-set size in the supplied source.

Therefore:

> Dataset size is a Phase 7 engineering choice, not an official requirement.

Recommended metrics:

```text
per-Skill recall
overall hit rate
wrong-Skill routing rate
no-trigger precision
```

Primary competition metric:

```text
Trigger Hit Rate ≥90%
```

---

# 12. Self-Test Requirement

The Track B source requires:

```text
Each Skill includes ≥20 self-test cases
```

Phase 7 minimum:

```text
6 Skills × 20 tests
= 120 self-tests minimum
```

Recommended target:

```text
24–30 tests per Skill
```

only if it does not delay completion.

The acceptance target remains:

```text
100% self-test pass rate
```

---

# 13. Self-Test Design by Skill

## Trajectory Guard

Cover:

```text
first valid action
contained run
same fingerprint after containment
new action before containment
blocked proposal never executes
identity normalization edge cases
```

---

## Progress Accounting

Cover:

```text
new evidence
duplicate evidence
world-state change
no world-state change
retrieval new identity
retrieval same identity
todo-only movement
postcondition progress
mixed delta cases
```

---

## Failure Detection

Cover:

```text
exact loop
non-loop similar actions
oscillation A-B-A-B
false oscillation
retrieval churn
useful recheck
generic no progress
threshold boundaries
```

---

## Execution Contract

Cover:

```text
step budget
tool budget
stall budget
oscillation budget
retrieval budget
side-effect budget
verification reserve
boundary at N-1 / N / N+1
```

---

## Approval Control

Cover:

```text
read-only no approval
high-impact approval required
denial
approval
stale approval
approval cannot be reused incorrectly
side effect executes exactly once
```

---

## Outcome Verification

Cover:

```text
verified healthy
failed unhealthy
stale generation
wrong resource identity
missing observation
accepted but not yet checked
unknown
fresh success
```

---

# 14. Multi-Agent Orchestration Layer

SP-A requires real collaboration, not merely six independent Skills.

Recommended role model:

```text
Incident Commander
    owns overall goal / plan

Diagnosis Agent
    owns evidence collection / hypothesis testing

Operations Agent
    owns proposed remediation actions

Verification Agent
    owns fresh postcondition checks
```

Optional:

```text
Knowledge Agent
```

only if retrieval is a meaningful part of the scenario.

---

# 15. Orchestration Contract

Define a shared message schema.

The SP-A source asks for:

```text
Unified trigger word system
shared communication / message schema
```

Recommended collaboration envelope:

```json
{
  "collaboration_id": "...",
  "task_id": "...",
  "subtask_id": "...",
  "agent_role": "...",
  "intent": "...",
  "objective": "...",
  "evidence_refs": [],
  "proposed_action": null,
  "expected_postcondition": null,
  "status": "...",
  "handoff_to": null
}
```

This schema is illustrative and may be adapted.

Do not put hidden reasoning / chain-of-thought into the message schema.

Use:

```text
decisions
evidence
plans
actions
status
```

not private reasoning traces.

---

# 16. Planning Layer

SP-A explicitly calls for:

```text
task decomposition
long-horizon planning
```

Recommended implementation:

```text
Goal
    ↓
Task Graph / Plan
    ↓
Subtasks
    ↓
Role assignment
    ↓
Execution
    ↓
Replan only when evidence changes
```

Example:

```text
Goal: Restore service health safely

1. Establish current health
2. Identify likely failure domain
3. Collect confirming evidence
4. Select remediation
5. Request approval if high impact
6. Execute remediation
7. Verify postcondition
8. Close incident
```

ReasonFuse should observe the runtime trajectory but should not replace the Planner.

---

# 17. Agent / ReasonFuse Responsibility Boundary

This must be explicit in architecture and documentation.

## Agents own

```text
interpretation
planning
role coordination
hypothesis formation
tool selection proposals
natural-language collaboration
```

## ReasonFuse owns

```text
deterministic trajectory control
progress accounting
failure detection
execution budget
containment
approval integration
outcome verification
```

This separation is one of the strongest technical differentiators.

---

# 18. Collaborative Stress Testing / Fault Injection

SP-A explicitly asks for:

```text
adversarial gameplay simulation
swarm emergence observation
collaborative stress testing / fault injection
```

Phase 7 should implement a **bounded demo-grade subset**.

Recommended fault library:

```text
F1  Repeated diagnostic request
F2  Oscillating agent handoff
F3  Multiple agents retrieve equivalent evidence
F4  Operations Agent proposes high-impact action too early
F5  Side effect returns accepted but world remains unhealthy
F6  Stale verifier observation
F7  Conflicting agent conclusions
F8  Budget exhaustion
```

---

# 19. Adversarial / Collaboration Cases

At least three collaboration-specific cases should exist beyond single-agent ReasonFuse tests.

Recommended:

### C-ADV-001 — Ping-Pong Handoff

```text
Diagnosis → Operations → Diagnosis → Operations
```

without new evidence.

Expected:

```text
oscillation / no-progress detected
collaboration bounded
```

---

### C-ADV-002 — Duplicate Retrieval Swarm

Multiple agents ask different questions that normalize to the same evidence.

Expected:

```text
retrieval churn recognized
duplicate work bounded
```

---

### C-ADV-003 — Premature Remediation

Operations Agent proposes restart before minimum diagnostic evidence.

Expected:

```text
planner / policy rejects or defers
and/or approval required
ReasonFuse does not falsely mark progress
```

---

# 20. Runtime Visualization

SP-A asks for runtime visualization and monitoring.

Do not build a huge dashboard.

Build one compact judge-facing view.

Recommended columns:

```text
Time
Agent
Subtask
Action
ReasonFuse Skill
Decision
Progress
Outcome
```

Example:

| Step | Agent | Action | ReasonFuse | Result |
|---|---|---|---|---|
| 1 | Diagnosis | service_status | Trajectory Guard | ALLOW |
| 2 | Diagnosis | db_health | Progress Accounting | NEW EVIDENCE |
| 3 | Operations | restart | Approval Control | APPROVAL REQUIRED |
| 4 | Verification | service_status | Outcome Verification | VERIFIED |

Optional panels:

```text
current plan
contract budget
detector status
pending postcondition
```

---

# 21. Phase 7 Demo Narrative

Use one unified main demo.

## Act 1 — Intent

```text
Restore checkout health safely.
```

---

## Act 2 — Decomposition

Incident Commander creates subtasks:

```text
diagnose
confirm
remediate
verify
```

---

## Act 3 — Collaboration

Diagnosis and Operations agents coordinate.

Inject one controlled collaboration failure:

```text
oscillating handoff
or
duplicate evidence retrieval
```

ReasonFuse intervenes.

---

## Act 4 — High-Impact Action

Operations proposes:

```text
restart_service
```

Approval Control activates.

---

## Act 5 — Verification

Restart returns:

```text
accepted
```

ReasonFuse does not declare success.

Verification Agent performs fresh read.

Outcome:

```text
OUTCOME_VERIFIED
```

---

## Act 6 — Monitoring

Show:

```text
agent collaboration trace
ReasonFuse interventions
final verified result
self-test / trigger-rate summary
```

---

# 22. Phase 7 Business Story

Phase 7 should avoid sounding like:

> six generic Skills glued together.

Instead:

> **ReasonFuse gives multi-agent systems a deterministic reliability backbone.**

Business value:

```text
less duplicate agent work
bounded collaboration
safer high-impact actions
less runaway orchestration
verified real-world outcomes
auditable collaboration
```

Primary user:

```text
teams deploying multi-agent systems into real operational workflows
```

---

# 23. Phase 7 Workstreams

Use these workstreams:

```text
7A  Phase 6 Freeze & Handoff
7B  SP-A Competition Adapter
7C  Six Formal Skill Packages
7D  Trigger Router + Trigger Evaluation
7E  Multi-Agent Orchestration
7F  Collaborative Fault Injection
7G  Self-Test / Acceptance Harness
7H  Packaging / Installability
7I  Runtime Visualization
7J  Competition Demo / Story
7K  Final Submission Audit
```

---

# 24. 7A — Phase 6 Freeze & Handoff

Before Phase 7 work:

```text
[ ] record final Phase 6 commit SHA
[ ] preserve Microsoft submission artifact
[ ] tag / branch Phase 6 version
[ ] confirm ReasonFuse core tests PASS
[ ] copy Phase 6 public evidence forward
[ ] do not mix Phase 7 changes into submitted Phase 6 branch
```

Recommended Git strategy:

```text
main / phase6-submitted
        ↓
phase7-1010
```

Exact branch names are optional.

---

# 25. 7B — SP-A Competition Adapter

Add a thin layer that exposes ReasonFuse capabilities in competition-friendly contracts.

Adapter responsibilities:

```text
normalize competition request
route to correct Skill
translate shared message schema
preserve collaboration IDs
return Skill result
```

Adapter must not duplicate core logic.

Wrong:

```text
copy engine.py logic into each Skill
```

Correct:

```text
Skill wrapper
    ↓
existing ReasonFuse core
```

---

# 26. 7C — Six Formal Skill Packages

For each Skill:

```text
[ ] SKILL.md
[ ] adapter / callable entry
[ ] input schema
[ ] output schema
[ ] example
[ ] ≥20 self-tests
[ ] trigger examples
[ ] negative trigger examples
[ ] main-scenario integration
```

All six must be genuinely used in the final E2E.

Do not submit six Skills where only two appear in the demo.

---

# 27. 7D — Trigger Router + Evaluation

Build:

```text
trigger_router
trigger_dataset
trigger_eval
```

Output:

```text
per-Skill hit rate
overall hit rate
confusion summary
```

Competition gate:

```text
overall trigger hit rate ≥90%
```

Recommended internal target:

```text
≥95%
```

to leave margin.

This ≥95% is an engineering target, not an official rule.

---

# 28. 7E — Multi-Agent Orchestration

Implement:

```text
intent intake
task decomposition
plan
role assignment
shared collaboration state
handoff
result aggregation
```

Keep the orchestration layer small and inspectable.

The point is not to compete on “maximum agent count.”

The point is:

> **ReasonFuse makes collaboration reliable.**

---

# 29. Orchestration Framework Open Question

The supplied SP-A brief gives examples such as:

```text
AgentVerse
AutoGen
etc.
```

and describes the use of open-source multi-agent orchestration frameworks.

The source does not explicitly state whether Microsoft Agent Framework is accepted as an equivalent in this competition.

Therefore Phase 7 must treat this as an **open organizer-compatibility question**.

Preferred order:

```text
1. confirm official acceptance of the chosen orchestration framework
2. if accepted, reuse the Phase 6 Microsoft/Agent Framework stack
3. if not accepted, add a thin competition orchestration adapter using an accepted open-source framework
```

Do not rewrite ReasonFuse core either way.

---

# 30. 7F — Collaborative Fault Injection

Implement controlled fixtures for at least:

```text
loop
oscillation
retrieval churn
premature side effect
postcondition failure
stale verification
```

Add collaboration-specific injections:

```text
agent handoff ping-pong
duplicate work across agents
conflicting agent decisions
```

Each fault should be:

```text
deterministic
resettable
safe
observable
```

---

# 31. 7G — Self-Test / Acceptance Harness

Create one command that runs all competition acceptance tests.

Example conceptual interface:

```text
phase7 verify
```

It should report:

```text
6/6 Skill packages found
≥20 tests per Skill
all self-tests PASS
trigger hit rate
main E2E PASS
package install test PASS
```

Do not require the judge to execute many unrelated commands.

---

# 32. 7H — Packaging / Installability

Track B requires an installable / packagable deliverable.

Phase 7 should produce one documented setup path.

Target experience:

```text
clone
    ↓
install dependencies
    ↓
configure minimal environment
    ↓
run self-tests
    ↓
run main demo
```

Avoid:

```text
manual undocumented cloud setup
hidden local files
private credentials
machine-specific paths
```

The final package should clearly identify:

```text
local-only mode
optional cloud mode
required secrets
reset command
test command
demo command
```

---

# 33. 7I — Runtime Visualization

Add the smallest useful UI / terminal view.

P0 display:

```text
current agent
current subtask
current action
ReasonFuse Skill
decision
progress
failure / approval / outcome
```

P0.5:

```text
graph view
timeline animation
agent relationship view
```

Do not block submission on P0.5.

---

# 34. 7J — Competition Demo / Story

Suggested 3–5 minute competition demo structure:

```text
0:00–0:30
Business problem

0:30–1:00
Intent + decomposition

1:00–2:00
Multi-agent collaboration

2:00–2:45
Injected failure + ReasonFuse containment

2:45–3:30
Approval + side effect

3:30–4:15
Fresh verification + verified outcome

4:15–5:00
6 Skills + test / trigger / packaging proof
```

If organizer imposes a shorter time limit, compress proportionally.

Do not assume 5 minutes is official unless final competition instructions say so.

---

# 35. 7K — Final Submission Audit

Submission cannot proceed until:

```text
[ ] ≥6 effective Skills
[ ] every Skill has SKILL.md
[ ] every Skill has supporting code/scripts
[ ] every Skill has ≥20 self-tests
[ ] all self-tests pass
[ ] trigger hit rate ≥90%
[ ] one unified SP-A scenario
[ ] main E2E demo works
[ ] task decomposition visible
[ ] multi-agent collaboration visible
[ ] fault injection visible
[ ] runtime monitoring visible
[ ] install / package path documented
[ ] business value clear
[ ] ReasonFuse core boundary clear
[ ] no unsupported competition claims
[ ] no secrets
```

---

# 36. Proposed Phase 7 Repository Shape

Illustrative:

```text
competition/
└── phase7/
    ├── README.md
    ├── skills/
    │   ├── trajectory_guard/
    │   ├── progress_accounting/
    │   ├── failure_detection/
    │   ├── execution_contract/
    │   ├── approval_control/
    │   └── outcome_verification/
    │
    ├── orchestration/
    │   ├── coordinator.py
    │   ├── roles.py
    │   ├── planner.py
    │   └── message_schema.py
    │
    ├── scenarios/
    │   ├── incident_recovery/
    │   └── faults/
    │
    ├── evaluation/
    │   ├── trigger_dataset.json
    │   ├── trigger_eval.py
    │   └── acceptance.py
    │
    ├── demo/
    │   └── ...
    │
    └── tests/
        └── ...
```

This is a construction recommendation, not an official competition filesystem requirement.

---

# 37. Phase 7 Development Order

Do not start by writing six `SKILL.md` files.

Correct order:

```text
Phase 6 freeze
    ↓
Confirm SP-A / framework compatibility
    ↓
Define unified scenario
    ↓
Define shared message schema
    ↓
Build orchestration skeleton
    ↓
Wrap existing ReasonFuse core as 6 Skills
    ↓
Wire all 6 into one E2E
    ↓
Add collaboration fault injection
    ↓
Build ≥20 self-tests per Skill
    ↓
Build trigger dataset / reach ≥90%
    ↓
Package / install test
    ↓
Visualization
    ↓
Presentation / final audit
```

---

# 38. Scope Control

Do not add:

```text
digital human avatar
multimodal generation
knowledge graph
fine-tuning
office social network
complex vector memory
large web dashboard
extra cloud platform
```

unless the selected final track or organizer instructions make them necessary.

Those belong to other Track B directions or optional polish.

SP-A should remain:

```text
orchestration
collaboration
stress testing
monitoring
reliability
```

---

# 39. Phase 7 P0 vs P0.5

## P0

```text
6 formal Skills
SKILL.md per Skill
20+ self-tests per Skill
100% pass
≥90% trigger hit rate
one unified SP-A pipeline
multi-agent decomposition / collaboration
fault injection
ReasonFuse intervention
outcome verification
runtime monitoring
installable package
```

## P0.5

```text
advanced graph visualization
additional agent roles
APIM canary reuse
Foundry IQ live integration
multiple incident scenarios
swarm visualization
extra adversarial simulations
```

P0.5 must never destabilize P0.

---

# 40. Phase 7 Completion Definition

Phase 7 is complete only when:

```text
1. ReasonFuse v5.0.0 core remains stable.

2. Six ReasonFuse Reliability Skills exist as formal competition packages.

3. Every Skill has SKILL.md + supporting implementation.

4. Every Skill has at least 20 self-tests.

5. All Skill self-tests pass.

6. Trigger hit rate is at least 90%.

7. One unified SP-A scenario uses all six Skills.

8. The scenario performs task decomposition and long-horizon planning.

9. Multiple role agents genuinely collaborate.

10. At least one collaborative failure is injected.

11. ReasonFuse deterministically detects / contains the failure.

12. A high-impact action follows approval control.

13. Final success is determined by fresh outcome verification.

14. Runtime collaboration and ReasonFuse decisions are observable.

15. The project is installable / packagable.

16. The competition story explains real-world business value.

17. Phase 7 changes do not invalidate the Phase 6 Microsoft submission.
```

---

# 41. Phase 7 Final Thesis

The competition submission should not be:

> **“Here are six AI Skills.”**

It should be:

> **“Here is a collaborative multi-agent system, and here are the six deterministic reliability Skills that keep its execution bounded, productive, safe, and verifiable.”**

The strongest final architecture is:

```text
Multi-Agent Collaboration
        ↓
ReasonFuse Reliability Skills
        ↓
Deterministic Runtime Control
        ↓
Real Tools
        ↓
Verified Outcome
```

That preserves the core ReasonFuse idea while satisfying the Track B / SP-A competition structure.

---

# 42. Phase 7 Handoff Rule

When Phase 7 begins:

> **Do not reopen architecture design discussions that Phase 1–6 already settled.**

The only valid Phase 7 questions are:

```text
How do we package the core as competition Skills?
How do we wire them into SP-A collaboration?
How do we prove ≥20 tests / Skill?
How do we achieve ≥90% trigger hit rate?
How do we make the E2E installable and demoable?
How do we tell the strongest competition story?
```

Everything else is scope pressure unless a real blocker proves otherwise.
