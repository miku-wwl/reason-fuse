# ReasonFuse — Microsoft Agent-a-thon Final Plan v5.0.0 — HACKATHON IMPLEMENTATION FREEZE

> **Positioning:** Runtime Progress Control for Open-Ended AI Agent Trajectories  
> **Architecture:** History-Safe / Primitive-Native / Local Tool Interception / Cost-Controlled Evidence  
> **Built on:** Microsoft Foundry + Microsoft Agent Framework + Foundry Toolbox / Foundry IQ + Azure API Management  
> **Core Rule:** Microsoft owns platform capabilities. ReasonFuse owns deterministic runtime progress control.  
> **Project Standard:** **Agent-a-thon / Hackathon-grade engineering proof — not production certification**  
> **Source of Truth:** **The current repository is authoritative. Documentation follows the implementation, not the reverse.**  
> **Architecture Status:** **FROZEN**  
> **Implementation Status:** **CORE IMPLEMENTED / LOCAL FREEZE COMPLETE / LIVE DEMO CAPTURE OPTIONAL**

---

# 0. Why v5.0.0 Exists

v5.0.0 deliberately changes the project-completion standard.

Previous plans gradually accumulated production-style evidence requirements:

```text
large repeated scenario benchmark
event-scale performance microbenchmark
large evaluator/reporting layer
full clean-start reproducibility of every supporting service
Judge UI
multi-person usability testing
production-style release evidence
```

Those are valid for a production reliability product, but they are **not required to prove the ReasonFuse idea in an Agent-a-thon**.

v5.0.0 therefore adopts this rule:

> **Spend engineering time and cloud budget only on evidence that materially helps a judge understand and trust the core idea.**

The goal is no longer:

```text
prove production readiness
```

The goal is:

```text
prove the architecture is real
prove the core behavior is correct
prove the Microsoft integration is genuine
prove the demo is understandable
prove the project can be reproduced enough for judging
avoid unnecessary Azure / LLM spend
```

This is not a downgrade of the core engineering standard.

It is a reduction of **evidence scale**, not a reduction of **correctness**.

---

# 1. v5.0.0 Governing Principles

## 1.1 Current repository wins

When an older architecture document conflicts with the final codebase:

```text
current implementation
+
verified behavior
+
current README/deployment path
```

wins over historical planning text.

Older requirements are retained only when they still provide clear competition value.

---

## 1.2 Core correctness stays strict

The following are **not optional**, even for a hackathon:

```text
history ownership correctness
AgentSession state persistence
Todo != objective progress
local middleware interception
bounded execution
side-effect approval
postcondition verification
deterministic containment
no false success from HTTP 202 / accepted=true
truthful claims about Foundry / Toolbox / IQ / APIM
```

Cost control must never be used to excuse a correctness defect.

---

## 1.3 Scale evidence is optional

The following are no longer P0 submission requirements:

```text
large automated benchmark runner
repeated paid or repeated agent runs
event-scale performance microbenchmark
p50/p95/p99 runtime benchmarking
large offline evaluator framework
6–8 person formal usability study
production SLOs
production load testing
production HA proof
production-grade rollback automation
```

They are future hardening work.

---

## 1.4 Local proof by default

Validation hierarchy:

```text
1. deterministic local unit/boundary tests
2. lightweight local behavior scenarios
3. only then, a small number of curated live Foundry demonstrations
```

Cloud execution is justified only when it proves something that cannot honestly be proven locally.

---

## 1.5 Demo evidence beats benchmark volume

For this project:

```text
one clear OFF / ON trajectory
+
one clear containment explanation
+
one real approval/postcondition flow
+
one genuine Microsoft integration trace
```

is more valuable than hundreds of repetitive runs that the judge will never inspect.

---

# 2. Product Thesis

ReasonFuse is:

> **A Microsoft Foundry-native runtime progress-control layer for open-ended AI agent trajectories where no correct execution path is known in advance.**

It asks:

```text
Did we gain new objective evidence?
Did the external world change?
Did retrieval add genuinely new information?
Are we repeating equivalent work?
Are we oscillating?
Did a side effect actually satisfy its postcondition?
```

When the answer repeatedly becomes “no”, ReasonFuse contains the run.

Primary line:

> **Foundry runs the agent. ReasonFuse decides whether the run is still making progress.**

---

# 3. Product Boundary

Microsoft Foundry / Agent Framework provide platform capabilities such as:

```text
agent hosting
identity / authorization primitives
conversation persistence
tool integration
knowledge integration
planning primitives
approval primitives
telemetry primitives
evaluation primitives
platform safety controls
```

ReasonFuse adds:

```text
objective-progress detection
trajectory no-progress control
exact-loop detection
oscillation detection
retrieval-churn detection
useful-recheck preservation
bounded execution
postcondition verification
behavioral containment
```

ReasonFuse does not need to become:

```text
a second conversation database
a custom RAG platform
a custom tool registry
a custom tracing platform
a multi-agent orchestration system
a production release platform
```

---

# 4. Effective Architecture — Current Repository Baseline

```text
User / Demo Client
       ↓
Azure API Management               optional live demo boundary
 ├─ Stable / Candidate pool
 ├─ session affinity
 └─ SSE pass-through
       ↓
Foundry Hosted Agent
       ↓
Responses 2.0.0
       ↓
ResponsesHostServer(
    history_source="agent_server"
)
       ↓
Agent Framework Agent
 ├─ AgentSession
 ├─ TodoProvider
 ├─ AgentModeProvider
 ├─ native Tool Approval
 └─ ReasonFuse Function Middleware
       ↓
Local Function / MCP invocation
       ↓
Foundry Toolbox / Foundry IQ / Operations tools
       ↓
ReasonFuse result normalization
       ↓
Outcome verification
       ↓
OTel / structured ReasonFuse telemetry
```

The deterministic ReasonFuse core is independent of whether a particular validation run is local or cloud-hosted.

---

# 5. Current Implementation Truth

The current repository already contains the important runtime pieces.

| Capability | v5.0.0 status |
|---|---|
| Hosted Agent entry point | **IMPLEMENTED** |
| Responses 2.0.0 hosting path | **IMPLEMENTED** |
| `history_source="agent_server"` | **IMPLEMENTED** |
| downstream `store=False` | **IMPLEMENTED** |
| AgentSession-backed ReasonFuse state | **IMPLEMENTED** |
| deterministic progress engine | **IMPLEMENTED** |
| Todo excluded from objective progress | **IMPLEMENTED** |
| exact-loop detector | **IMPLEMENTED** |
| oscillation detector | **IMPLEMENTED** |
| retrieval-churn detector | **IMPLEMENTED** |
| useful-recheck handling | **IMPLEMENTED** |
| bounded Run Contract | **IMPLEMENTED** |
| postcondition / outcome verifier | **IMPLEMENTED** |
| local Function Middleware | **IMPLEMENTED** |
| runtime-native approval configuration | **IMPLEMENTED** |
| structured telemetry | **IMPLEMENTED** |
| APIM 95/5 + affinity config | **IMPLEMENTED IN IAC** |
| lightweight 15-scenario validation spec | **PRESENT, SEMANTICALLY ALIGNED** |
| unit / boundary tests | **PRESENT** |
| exact dependency pins | **PRESENT** |
| build identity | **INTENTIONALLY OMITTED FROM FINAL CLAIMS** |
| Operations demo service source | **NOT SELF-CONTAINED IN CURRENT REPO** |
| large automated benchmark | **INTENTIONALLY NOT REQUIRED** |
| event-scale microbenchmark | **INTENTIONALLY NOT REQUIRED** |
| Judge UI | **INTENTIONALLY NOT REQUIRED** |
| production clean-start environment | **INTENTIONALLY NOT REQUIRED** |

This table is the v5 source-of-truth view.

---

# 6. Conversation and Runtime State Ownership

Canonical model conversation history:

```text
Foundry Agent Server
└─ conversation history / tool transcript
```

ReasonFuse deterministic runtime state:

```text
AgentSession
└─ reasonfuse_core_v1
```

Required hosted configuration:

```python
ResponsesHostServer(
    agent,
    history_source="agent_server",
)
```

and downstream model storage remains disabled:

```python
default_options = {
    "store": False,
}
```

v5 invariants:

```text
No duplicate canonical transcript store.
No prompt reconstruction of deterministic ReasonFuse state.
No second model-history owner.
```

---

# 7. Deterministic ReasonFuse State

Current state design is retained.

Important persisted domains include:

```text
run identity
contract limits/version
step/tool/side-effect counters
recent action fingerprints
recent actions
progress history
evidence identities
retrieval attempts
world-state snapshot
Todo snapshot
stall state
pending postcondition
verification reserve
containment state
fuse reason
last signals / last outcome
```

Invariant:

> **LLM context may be shortened or changed. ReasonFuse deterministic state must remain authoritative.**

Malformed persisted state must fail closed rather than silently resetting a dangerous counter.

---

# 8. Objective Progress Model

Objective progress remains:

```text
Evidence Delta
+
World-State Delta
+
Retrieval Delta
+
Postcondition Delta
```

Planning signal:

```text
Todo Delta
```

Todo changes alone must not become evidence that reality changed.

The implementation must continue ignoring noisy world-state fields such as:

```text
timestamps
request IDs
trace IDs
execution IDs
operation IDs
incidental counters
random identifiers
```

when they do not represent meaningful external progress.

---

# 9. Failure Detectors

## 9.1 Exact Loop

Fingerprint:

```text
SHA256(tool_name + canonical_json(args))
```

Purpose:

```text
detect repeated equivalent action proposals
without objective progress
```

---

## 9.2 Oscillation

Pattern:

```text
A → B → A → B
+
no objective progress
```

Purpose:

```text
detect cyclic switching between alternatives
without actually learning anything
```

---

## 9.3 Retrieval Churn

Pattern:

```text
different retrieval queries
+
equivalent normalized evidence
+
no new information
```

Purpose:

```text
prevent endless paraphrased search loops
```

---

# 10. Run Contract — v5 Reconciliation

The current repository default remains authoritative:

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

v5.0.0 does **not** require changing this default merely to make every specific detector label reachable first.

The current default is interpreted as an **aggressive containment profile**:

```text
no objective progress for a short bounded window
→ generic NO_PROGRESS may contain the run
before a more specific taxonomy label is reached
```

This is acceptable for the hackathon as long as the documentation is truthful.

### Detector-specific local validation

When the project wants to demonstrate a particular taxonomy label such as:

```text
EXACT_LOOP
OSCILLATING
```

a local test/scenario may instantiate a wider deterministic test contract, for example:

```yaml
max_stalled_steps: 4
required_objective_progress_interval: 4
```

This is a **test-policy override**, not a second architecture.

Therefore v5 removes the previous requirement that production/default parameters must be widened only to expose detector labels.

The project must not claim:

```text
"the default contract always classifies exact loop before generic no-progress"
```

because the current code does not support that claim.

---

# 11. Useful Recheck Preservation

ReasonFuse must preserve one bounded verification read after an accepted side effect.

Example:

```text
service_status(orders) → unhealthy
restart_service(orders) → accepted
service_status(orders) → fresh verification
```

This verification read is useful even if it repeats a prior read operation.

Useful recheck means:

```text
the recheck is justified
```

not:

```text
the side effect succeeded
```

---

# 12. Outcome Verification

ReasonFuse must never equate:

```text
HTTP 202
accepted=true
```

with:

```text
recovered / successful
```

Required flow:

```text
side-effect proposal
 ↓
approval
 ↓
execution accepted
 ↓
persist pending postcondition
 ↓
reserve one verification opportunity
 ↓
fresh verifier read
 ↓
OutcomeVerifier
 ↓
OUTCOME_VERIFIED
or POSTCONDITION_FAILED
or OUTCOME_UNKNOWN
```

This remains a P0 product feature because it is one of the strongest demo differentiators.

---

# 13. Human Approval

High-impact action:

```text
restart_service
```

must continue to require explicit runtime-native approval.

For Agent-a-thon evidence, one clean live demonstration is enough:

```text
1. action proposed
2. execution pauses
3. approval is granted
4. exact action executes
5. verification follows
```

Production-grade approval audit databases, approval-service redundancy, or large approval test matrices are out of scope.

---

# 14. Local Tool Interception

ReasonFuse-critical tools must continue through local Function Middleware.

Required conceptual sequence:

```text
proposal
 ↓
ReasonFuse pre-call decision
 ↓
ALLOW / BLOCK
 ↓
local tool invocation if allowed
 ↓
result normalization
 ↓
ReasonFuse post-call observation
```

`read_runtime_state` remains a deliberate observability exception.

It must remain callable after containment and therefore must **not** be used as evidence that operational Exact Loop / Oscillation interception works.

---

# 15. Foundry Toolbox / Foundry IQ Boundary

The current repository may consume externally prepared Toolbox / IQ resources through environment configuration.

For v5 hackathon scope, it is **not required** that the repository independently provision every Foundry Toolbox or Knowledge Base asset from zero.

Required truthfulness rule:

```text
If an external Foundry resource is required,
document it as an external demo prerequisite.
```

Do not claim:

```text
"one-command full environment reconstruction"
```

unless the repository actually provides it.

ReasonFuse retrieval logic should continue consuming normalized evidence identities rather than depending on unstable provider-specific metadata.

---

# 16. Operations Tool Boundary

The repository currently contains infrastructure expectations for an Operations service, but not a fully self-contained Operations API source package matching every infrastructure assumption.

Under v5 this is not automatically a submission blocker.

Acceptable hackathon options:

```text
Option A
→ restore a tiny local/demo Operations API

Option B
→ use an already deployed external demo endpoint
→ document it clearly as a prerequisite

Option C
→ use deterministic local fixtures for core behavior
→ use only a small live integration subset in the final demo
```

What is not acceptable:

```text
claiming the repository creates a complete Operations service
when it does not
```

---

# 17. APIM Sticky Canary

The current repository already contains meaningful APIM work:

```text
95/5 Stable/Candidate weighting
session affinity
SSE pass-through behavior
body logging restrictions
```

v5 keeps this as a **strong Microsoft-platform integration bonus**, but not as a required production release system.

For submission, any one of the following can be sufficient:

```text
live sticky-affinity proof
or
clear APIM policy/IaC walkthrough in the video
or
captured trace/screenshot from a successful prior run
```

Do not spend significant cloud budget repeatedly exercising the same canary behavior after it has already been demonstrated.

Automatic production rollback is P1/future work.

---

# 18. Telemetry and Evidence

ReasonFuse structured telemetry should continue exposing useful decision fields such as:

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

For Agent-a-thon judging, telemetry has two jobs:

```text
1. make the containment decision explainable
2. prove the middleware really observed the runtime
```

A full production monitoring dashboard is not required.

Terminal output, structured logs, Foundry/Application Insights traces, and video overlays are acceptable evidence.

---

# 19. Dependency Reproducibility

Keep:

```text
pyproject.toml
uv.lock
requirements.txt
exact dependency pins
```

This is low-cost and valuable.

Do not upgrade Agent Framework / Foundry packages immediately before the final submission unless a blocking issue requires it.

---

# 20. Build Identity — v5 Final Decision

The previous `build_identity.json` was stale after repository cleanup and source-scope
reduction. It has been removed from the final lightweight package.

The runtime handles a missing manifest by returning no build-identity claim. This is
intentional: the final hackathon package does not present an unverified provenance
manifest as current lineage.

If a later submission requires provenance, regenerate a new manifest from the exact
final commit and verify it as a separate release step. It must not be recreated from
an older evidence snapshot.

```text
current v5 rule: no build_identity.json means no build-lineage claim
```

v5 does not require a production-grade artifact provenance system.

It requires only that any provenance claim made to judges be true.

---

# 21. v5 Validation Strategy — Cost Controlled

The previous large benchmark model is retired from P0.

v5 uses three evidence layers.

---

## Layer A — Unit / Boundary Tests

Purpose:

```text
prove deterministic core invariants quickly and repeatedly
```

Must cover the important behaviors already represented in the repository, including:

```text
canonical fingerprinting
objective-progress calculation
noise filtering
Todo-only behavior
exact-loop logic
oscillation logic
retrieval churn
side-effect budget reservation
pending verification persistence
postcondition success/failure/unknown
malformed state fail-closed behavior
```

Cost:

```text
local only
no Azure
no LLM
```

---

## Layer B — Corrected Lightweight Scenario Suite

Retain the current repository philosophy:

> **15 different behavioral scenarios, one pass each, not hundreds of repeated runs.**

Each scenario records:

```text
scenario ID
initial state
contract profile if overridden
tool/action sequence
actual detector/result
actual outcome
PASS / FAIL / NOT VERIFIED
evidence location
```

A failed scenario must not be hidden by rerunning it until it passes.

---

## Layer C — Small Curated Live Foundry Proof

Only a small number of live runs are required.

Recommended signature evidence set:

### LIVE-1 — Hosted core flow

Prove:

```text
Hosted Agent is real
Agent Server history path is real
ReasonFuse middleware is active
ReasonFuse state is available across the run
```

### LIVE-2 — Containment

Prove one clear no-progress containment path:

```text
repeat / churn / oscillation-like behavior
→ ReasonFuse blocks or contains
→ telemetry explains why
```

The exact failure label is less important than a truthful demonstration of deterministic containment.

### LIVE-3 — Approval + Outcome Verification

Prove:

```text
high-impact action requires approval
accepted action is not treated as success
fresh verification determines final outcome
```

### LIVE-4 — Microsoft knowledge/tool integration, only if needed

One genuine Foundry Toolbox / Foundry IQ interaction is enough to prove the platform integration.

Do not repeatedly rerun paid scenarios solely to create benchmark volume.

---

# 22. Corrected 15-Scenario Acceptance Set

The current `benchmark/15-scenarios.md` strategy is retained with the semantic corrections
listed below already applied.

The corrected v5 set is:

| ID | Category | Scenario | Expected result |
|---|---|---|---|
| H-001 | Healthy | unhealthy → approved restart → fresh healthy recheck | `OUTCOME_VERIFIED`, not contained |
| H-007 | Healthy Retrieval | second retrieval adds genuinely new normalized evidence | retrieval delta true, no churn |
| H-010 | Healthy Progress | diagnostic result introduces a new discriminating evidence key | objective progress true |
| NP-001 | Planning Only | Todo changes repeatedly without external evidence | Todo delta true; objective progress false; bounded `NO_PROGRESS` under focused contract |
| EL-001 | Exact Loop | same DNS proposal repeated under detector-observation contract | `EXACT_LOOP` |
| EL-005 | Exact Loop | same DB health proposal repeated under detector-observation contract | `EXACT_LOOP` |
| EL-009 | Exact Loop | same service status proposal repeated under detector-observation contract | `EXACT_LOOP` |
| OS-001 | Oscillation | DNS ↔ service probe cycle without progress | `OSCILLATING` |
| OS-007 | Oscillation | service ↔ database probe cycle without progress | `OSCILLATING` |
| OS-012 | Oscillation | two supported operational probes alternate without progress | `OSCILLATING` |
| RC-001 | Retrieval Churn | three different queries return equivalent normalized evidence | `RETRIEVAL_CHURN` |
| RC-010 | Retrieval Churn | another query family returns the same evidence set | `RETRIEVAL_CHURN` |
| RC-020 | Retrieval Churn | rollback/release queries return equivalent evidence | `RETRIEVAL_CHURN` |
| OF-001 | Outcome Failure | restart accepted, fresh service verification unhealthy | `POSTCONDITION_FAILED` |
| OF-002 | Outcome Unknown/Failure | accepted side effect followed by invalid/unavailable/stale verification | `OUTCOME_UNKNOWN` or documented failed postcondition according to fixture |

Important corrections from the current scenario file:

```text
Do not call Todo-only changes healthy objective progress.
Do not use read_runtime_state to prove Exact Loop.
Do not use read_runtime_state as one side of an operational Oscillation test.
Use a wider local test contract when a specific detector label must be observed.
```

---

# 23. What v5 Explicitly Removes From P0

The following are **not required for Agent-a-thon submission**:

```text
large scenario dataset
repeated cloud runs
automated benchmark runner
large benchmark aggregation
event-scale performance microbenchmark
p50/p95/p99 engine performance study
throughput benchmarking
memory profiling report
full FoundryEvals harness
formal LocalEvaluator framework
6–8-person usability experiment
custom Judge Mode web application
production-ready dashboard
automatic canary rollback
full clean-room recreation of every external Foundry asset
production SLO / SLA proof
load test
chaos test
HA/DR test
```

这些扩展不属于本 v5 hackathon 包，也不作为后续交付任务。

---

# 24. Minimal Submission Evidence Package

ReasonFuse v5 is competition-ready when the project has the following evidence.

## Code evidence

```text
[x] unit/boundary tests pass
[x] source compiles
[x] dependency lock/pins are consistent
[x] corrected 15-scenario spec matches actual semantics
[x] no knowingly stale evidence is presented as current
```

## Local behavior evidence

```text
[ ] healthy progress demonstrated
[ ] Todo-only is shown as non-objective progress
[ ] exact loop demonstrated locally
[ ] oscillation demonstrated locally
[ ] retrieval churn demonstrated locally
[ ] outcome verification success demonstrated
[ ] failed/unknown postcondition demonstrated
```

## Live Microsoft evidence

```text
[ ] Hosted Agent run captured
[ ] local ReasonFuse middleware behavior visible in hosted flow
[ ] one approval flow captured
[ ] one genuine Toolbox/IQ/tool integration captured if used in the submission claim
[ ] APIM canary/affinity shown if included in the final story
```

## Presentation evidence

```text
[x] README matches the final repository
[ ] architecture diagram matches the implemented system
[ ] final demo/video clearly distinguishes platform capability from ReasonFuse capability
[ ] final video fits the competition time limit
```

That is enough.

---

# 25. Demo Story

The final demo should optimize for judge comprehension, not architecture density.

Recommended order:

```text
0:00–0:25
Problem + OFF behavior

0:25–1:05
ReasonFuse ON
objective progress = 0
containment decision

1:05–1:40
Planning changed, reality did not
Todo != objective progress

1:40–2:15
Approved side effect
accepted != success
fresh postcondition verification

2:15–2:40
Microsoft integration proof
Hosted Agent / Toolbox / IQ / tracing / APIM as applicable

2:40–3:00
Local validation evidence + close
```

Core sentence:

> **Planning changed. Reality did not.**

Closing sentence:

> **Foundry runs the agent. ReasonFuse decides whether the run is still making progress.**

---

# 26. Judge Explanation Model

A separate Judge UI is optional.

The same information may be shown through:

```text
terminal output
trace panel
structured log card
video overlay
simple static HTML
README screenshot
```

Minimum fields when a run is contained:

```text
ReasonFuse           BLOCK
Objective Progress   0
Evidence Delta       0
World-State Delta    0
Retrieval Delta      0
Todo Delta           +1 or 0
Useful Recheck       YES / NO
Fuse Reason          <reason>
```

The judge should be able to understand the decision in seconds.

---

# 27. Cost-Control Policy

This is now an explicit project rule.

## Default

```text
local deterministic validation
```

## Use Azure / LLM only when

```text
proving Hosted Agent integration
proving native approval behavior
proving Foundry Toolbox / IQ integration
capturing final tracing evidence
recording final demo footage
```

## Avoid

```text
repeated cloud benchmark loops
hundreds of LLM calls for deterministic logic
keeping demo infrastructure running unnecessarily
rerunning already-proven scenarios only for volume
production load tests
```

After final evidence is captured, expensive supporting resources may be stopped/deallocated where practical.

---

# 28. Repository Standard for v5

The repository does not need to grow into a production monorepo.

Current compact structure is acceptable:

```text
reason-fuse/
├── README.md
├── azure.yaml
├── pyproject.toml
├── requirements.txt
├── uv.lock
│
├── src/
│   ├── main.py
│   └── reasonfuse/
│       ├── agent.py
│       ├── main.py
│       ├── telemetry.py
│       ├── core/
│       └── validation/
│
├── tests/
│   ├── unit/
│   ├── local_wiring.py
│   └── local_history_audit.py
│
├── benchmark/
│   └── 15-scenarios.md
│
├── infra/
│   ├── APIM
│   ├── identity
│   ├── monitoring
│   └── supporting demo infrastructure
│
└── scripts/
    ├── bootstrap
    └── safe terraform plan
```

Add files only when they improve one of:

```text
correctness
demo reproducibility
judge clarity
truthfulness
```

Do not add folders merely to make the project look larger.

---

# 29. P0 / Optional Polish / Explicit Scope Boundary

## P0 — Agent-a-thon submission

```text
Hosted Agent path
history_source="agent_server"
store=False

AgentSession state
TodoProvider / AgentModeProvider
native approval

ReasonFuse local middleware
objective progress
bounded Run Contract
Exact Loop logic
Oscillation logic
Retrieval Churn logic
Useful Recheck
Outcome Verification

local unit/boundary tests
corrected lightweight 15-scenario suite
small curated hosted evidence set
structured telemetry
README + architecture diagram
final demo/video
```

## P0.5 — polish if time remains

```text
APIM sticky-canary live proof
small static Judge view
one additional realistic incident
simple validation report generation
Foundry trace screenshots
```

## Not part of this hackathon package

```text
No separate production-hardening track is maintained in this repository.
The final scope is the local deterministic core, the lightweight scenario list,
the optional bounded Hosted Agent demonstration, and the final presentation.
```

---

# 30. v5 Final Correctness Invariants

ReasonFuse hackathon P0 is correct only if:

```text
1. Foundry Agent Server remains canonical conversation-history owner.
2. downstream model history storage remains disabled.
3. ReasonFuse deterministic state lives in AgentSession.
4. Todo changes alone never count as objective progress.
5. ReasonFuse-critical operational tools pass local Function Middleware.
6. read_runtime_state remains observability-only.
7. generic NO_PROGRESS and specific detector labels are documented according to the contract actually used.
8. detector-specific tests may use an explicit wider local test contract.
9. accepted side effects do not count as verified success.
10. required side effects reserve bounded verification capacity.
11. failed or unavailable verification does not become success.
12. R2 restart requires explicit approval in the demonstrated flow.
13. containment logic remains deterministic.
14. retrieval evidence is normalized before progress comparison.
15. exact dependency pins remain in the repository.
16. external demo prerequisites are documented honestly.
17. local fixtures are never presented as live Foundry proof.
18. stale evidence artifacts are regenerated, removed, or clearly excluded from claims.
19. README and video claims match the actual repository.
20. no production-readiness claim is made without production evidence.
```

---

# 31. Required Closure Before Submission

These are the remaining submission activities, not repository repair defects.

## Repository closure

```text
[x] Correct benchmark/15-scenarios.md semantics.
    - Todo-only is not healthy objective progress
    - read_runtime_state is not used as detector evidence
    - detector-specific contract override is documented

[x] Remove stale build_identity.json from the final evidence claims.

[x] Make README truthful about external Operations / Toolbox / IQ prerequisites.

[x] Run existing unit/boundary/local checks on the current freeze.

[ ] Capture a small final live Foundry evidence set, only if the final submission
    claims live Hosted Agent behavior.

[ ] Record the final competition demo/video.
```

## Nice to have

```text
[ ] APIM sticky-affinity screenshot/trace
[ ] tiny static Judge display
[ ] one consolidated validation-results.md
[ ] final architecture image
```

## Do not spend time on

```text
[ ] large repeated benchmark
[ ] event-scale performance benchmark
[ ] production load test
[ ] large dashboard
[ ] new database
[ ] multi-agent architecture
[ ] new governance layer
[ ] Kubernetes / service mesh
[ ] infrastructure added only for visual complexity
```

---

# 32. Competition Readiness Gate — v5

ReasonFuse is ready for Agent-a-thon submission when:

```text
Architecture
= FROZEN

Core Runtime
= PASS

Core Tests
= PASS

15 Lightweight Scenarios
= SEMANTICALLY CORRECT; EXECUTION REPORT PENDING

Hosted Foundry Proof
= NOT INCLUDED IN THIS LOCAL FREEZE

Approval + Outcome Verification
= LOCALLY IMPLEMENTED; LIVE CAPTURE OPTIONAL

Microsoft Integration Claims
= BOUNDED AND TRUTHFUL; LIVE EVIDENCE REQUIRED FOR LIVE CLAIMS

README
= CURRENT

Demo / Video
= PENDING FINAL RECORDING
```

This final package intentionally does not include:

```text
large repeated benchmark suites
event-scale performance studies
production load testing
formal production certification
```

---

# 33. Architecture Freeze — FINAL v5.0.0

The architecture is frozen around the implementation that already exists.

Frozen:

```text
Foundry Agent Server history ownership
AgentSession ReasonFuse state
primitive-native Agent Framework composition
local Function Middleware interception
objective-progress model
Todo as planning-only signal
Exact Loop / Oscillation / Retrieval Churn logic
bounded execution
Useful Recheck
Outcome Verification
native approval
normalized retrieval evidence
structured telemetry
Foundry integration boundary
APIM canary configuration where used
```

Allowed from here:

```text
bug fixes
scenario/test corrections
README corrections
small demo fixtures
small integration fixes
trace/evidence capture
visual polish
video editing
submission packaging
```

Do not reopen architecture to add:

```text
new persistence layers
new orchestration frameworks
new governance systems
multi-agent topology
large benchmark infrastructure
production release machinery
new Azure services added only to look sophisticated
```

Final principle:

> **ReasonFuse v5.0.0 optimizes for proof, clarity, and correctness — not production-scale ceremony.**

Primary line:

> **Foundry runs the agent. ReasonFuse decides whether the run is still making progress.**
