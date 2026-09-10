# ReasonFuse Phase 3 — Evidence & Benchmark Construction Prompt

> **Purpose:** Build the benchmark, evaluation, dataset, measurement, and reporting system that measures the already independently validated Phase 2 ReasonFuse core with real evidence.  
> **Audience:** GPT-6 Astra / coding agent  
> **Phase:** 3 — Evidence & Benchmark  
> **Expected effort:** 8–10 hours  
> **Prerequisite:** Phase 2 ReasonFuse Core independent verification = **PASS**  
> **Architecture status:** FROZEN — do not redesign ReasonFuse  
> **Primary Exit Gate:** `15 curated scenarios × 1 repetition = 15 completed runs + confusion matrix + measured metrics`

---

# 0. Current Repository Handoff (2026-09-09)

Work in:

```text
D:\workshop\sep\reason-fuse
```

This is the repository-root prompt
`ReasonFuse_Phase3_Evidence_Benchmark_Construction_Prompt.md`, not a nested
`_Phase3` project. The Phase 3 agent is a benchmark constructor. Do not repeat
the completed Phase 2 construction or independent verification, and do not
rewrite their reports or indexes.

The authoritative Phase 2 handoff is:

```text
docs/phases/phase-02-core/report.md
docs/phases/phase-02-core/open-questions.md
docs/phases/phase-02-core/verification-report.md
docs/phases/phase-02-core/verification-open-questions.md
```

The independent index reports:

```text
INDEPENDENT_PHASE2_VALIDATION_PASS
```

The Phase 2 handoff is report-based. The superseded evidence indexes and old
learning intermediates were intentionally removed; do not recover or review
them. Use `verification-report.md` for the independent Phase 2 result and
`verification-open-questions.md` for its bounded caveats.

## Phase 2 baseline to preserve

Phase 2 P0 has already passed the required deterministic gates:

```text
OFF / ON                  PASS
Exact Loop                PASS
Oscillation               PASS
Retrieval Churn           PASS (deterministic Toolbox fixture)
Useful Recheck            PASS
Run Contract              PASS
Outcome Failure           PASS
Outcome Success           PASS
Outcome Unknown           PASS
Middleware / Compatibility PASS
Clean-start / final reset PASS
```

The final captured runtime was enabled ON with contract `{}` on both active
stable and candidate agents. The final package identity was audited and both
agents reported the same package content hash. Read the current capture and
index; do not assume these values from local `HEAD` alone.

Phase 3 consumes the already frozen Phase 2 handoff. This benchmark is a local
deterministic measurement profile; it does not change runtime architecture or
turn local fixture results into broader platform claims.

## Execution conventions

The validated workflow is Windows PowerShell with Python 3.13:

```powershell
Set-Location D:\workshop\sep\reason-fuse
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe ...
```

Use `scripts/verification_command.py <label> -- <command>` for every material
command so stdout, stderr, exit status, timestamp and source hashes are
retained. Use explicit UTC batch names such as:

```text
verification-<UTC>-phase3-benchmark
```

Keep raw Phase 3 evidence in a disposable system-temporary directory such as:

```text
%TEMP%/reasonfuse-phase3/verification-<UTC>/
```

Do not create new benchmark evidence under the repository's deleted `evidence`
tree. Inspect `git status -sb` before work; retain only the curated dataset,
code, and Markdown report required for review.

---

# 1. Mission

Phase 3 does not add new architecture.

Phase 3 turns the working ReasonFuse core into measurable competition evidence.

Your job is to build a reproducible evaluation system that answers:

```text
Does ReasonFuse detect harmful no-progress trajectories?

Does it preserve healthy investigation?

Does it preserve useful rechecks?

Does it detect failed real-world outcomes?

How quickly does it contain failures?

What behavior changes when ReasonFuse is ON versus OFF?
```

The result must be based on real execution, not hypothetical estimates.

---

# 2. Hard Prerequisite

Before changing code, inspect all of:

```text
docs/phases/phase-02-core/verification-report.md
docs/phases/phase-02-core/verification-open-questions.md
ReasonFuse_Phase2_Core_Verification_Prompt.md
```

Required:

```text
PHASE 2 RESULT: PASS
```

At minimum:

```text
OFF/ON PASS
Exact Loop PASS
Oscillation PASS
Retrieval Churn PASS
Useful Recheck PASS
Run Contract PASS
Outcome Verification PASS
```

If the independent Phase 2 report or hashed index does not show the required
PASS result:

```text
STOP
```

Do not create a benchmark for an unvalidated core. Do not rerun Phase 2 merely
to replace a report or to regenerate deleted intermediate evidence.

---

# 3. Phase 3 Scope

Build exactly these evidence layers:

```text
A. Versioned benchmark dataset
B. Deterministic scenario runner
C. 15-scenario suite
D. 1 repetition per scenario
E. LocalEvaluator / deterministic evaluator
F. Confusion matrix
G. Core reliability metrics
H. OFF/ON impact comparison
I. 10,000-event microbenchmark
J. Reproducible report artifacts
```

The benchmark measures the frozen Phase 2 core. It is not a vehicle to add
detectors, replace the middleware, introduce a production database, add a new
transport, or promote deterministic fixtures to Foundry IQ/production proof.
Do not redesign runtime architecture.

The Phase 3 implementation may add benchmark-only code under `benchmark/` and
`scripts/`; raw execution output belongs in a disposable system-temporary
directory, and it must not alter the
Phase 2 runtime semantics without opening a separately recorded regression and
revalidation boundary.

---

# 4. Frozen Benchmark Design

The canonical Phase 3 dataset is:

```text
3 Healthy Investigations
3 Exact Loop
3 Oscillation
3 Retrieval Churn
3 Outcome Failure
--------------------------------
15 scenarios
```

Run each scenario:

```text
1 repetition
```

Total:

```text
15 × 1 = 15 runs
```

Do not silently expand this target into a cloud-scale regression run. Larger
offline or production regressions belong to a separately authorized phase.

If an external service outage blocks completion, record the incomplete run count explicitly.

---

# 5. Evaluation Philosophy

ReasonFuse runtime is path-agnostic.

The benchmark must not require the agent to follow one exact reasoning path unless the scenario itself requires one.

ReasonFuse LocalEvaluator must primarily evaluate:

```text
expected failure class
expected containment
expected useful recheck behavior
expected outcome state
healthy completion preservation
```

Do not define success as:

```text
agent matched one exact tool sequence
```

unless the test specifically targets tool selection correctness.

---

# 6. Repository Structure

Create or extend:

```text
benchmark/
├── datasets/
│   ├── reasonfuse_v2.jsonl
│   ├── schema.json
│   └── README.md
│
├── scenarios/
│   ├── healthy/
│   ├── exact_loop/
│   ├── oscillation/
│   ├── retrieval_churn/
│   └── outcome_failure/
│
├── runners/
│   ├── run_suite.py
│   ├── run_single.py
│   └── reset_scenario.py
│
├── evaluators/
│   ├── local_evaluator.py
│   ├── confusion_matrix.py
│   └── impact_metrics.py
│
├── microbenchmark/
│   └── run_microbenchmark.py
│
├── reports/
│   ├── raw/
│   ├── normalized/
│   ├── charts/
│   └── summary/
│
└── PHASE3_REPORT.md
```

Keep the implementation simple and reproducible.

---

# 7. Dataset Schema

Create a versioned scenario schema.

Each scenario should contain at least:

```text
scenario_id
scenario_version
category
description

initial_world_state
fault_configuration

user_prompt

expected:
  should_trip
  expected_failure_type
  expected_outcome
  expected_useful_recheck
  healthy_completion_expected

run_contract_version

toolbox_version
knowledge_base_version
agent_version
model_version if pinned
```

Optional:

```text
expected_tool_classes
forbidden_behavior
notes
difficulty
```

Do not encode the exact model reasoning chain.

---

# 8. Scenario IDs

Use deterministic IDs.

Example:

```text
H-001, H-007, H-018
EL-001, EL-005, EL-013
OS-001, OS-007, OS-018
RC-001, RC-010, RC-020
OF-001, OF-002, OF-015
```

Where:

```text
H  = Healthy
EL = Exact Loop
OS = Oscillation
RC = Retrieval Churn
OF = Outcome Failure
```

---

# 9. Healthy Investigation Design

Healthy scenarios are critical.

They are not filler.

Their purpose is to detect false positives.

Include healthy patterns such as:

```text
health check
→ side effect
→ health recheck

retrieval
→ new evidence
→ retrieval refinement

DNS
→ DB
→ DNS after new deployment

same tool
→ world state changed
→ same tool again

same tool
→ different semantically meaningful args

multiple diagnostics
→ objective evidence accumulates

unknown correct path
→ investigation still makes progress
```

At least several Healthy scenarios must deliberately resemble the failure patterns while still being legitimate.

Do not create only trivial healthy cases.

---

# 10. Exact Loop Scenarios

Create 3 representative loop patterns.

Variation dimensions may include:

```text
different tools
different argument shapes
same semantic args with canonical ordering differences
different no-progress thresholds
different world states
different result payloads that normalize to same evidence
```

Expected:

```text
should_trip = true
expected_failure_type = EXACT_LOOP
```

---

# 11. Oscillation Scenarios

Create 3 representative oscillation scenarios.

At minimum include:

```text
A → B → A → B
```

Variation may include:

```text
service_status ↔ database_health
dns_resolution ↔ service_status
retrieval ↔ health
deployment_check ↔ config_check
```

Include negative-control Healthy cases where the same repeated pattern is justified by new evidence.

---

# 12. Retrieval Churn Scenarios

Create 3 representative scenarios where query wording changes but effective
evidence does not.

Normalize based on:

```text
source_keys
citation_ids
chunk_ids optional
derived normalized content hashes optional
knowledge_base_version
```

Expected:

```text
should_trip = true
expected_failure_type = RETRIEVAL_CHURN
```

Include Healthy negative controls where one new source materially changes evidence.

---

# 13. Outcome Failure Scenarios

Create 3 representative scenarios where action execution is accepted but the
real-world postcondition fails.

Examples:

```text
restart accepted
→ service still unhealthy

config update accepted
→ config version unchanged

scale accepted
→ replica count unchanged

rollback accepted
→ deployment remains bad
```

For Phase 3, use only action types actually supported by the Phase 2 deterministic Operations API.

Do not invent unimplemented production capabilities merely to inflate scenario count.

Expected:

```text
expected_outcome = POSTCONDITION_FAILED
```

---

# 14. Scenario Diversity Requirement

Avoid creating superficial copies of one scenario with renamed services.

Each category should vary meaningful dimensions.

For every scenario category, record the variation dimension.

Example:

```text
failure trigger
tool family
state transition
argument normalization
evidence shape
threshold proximity
side-effect presence
```

The benchmark should challenge the detector, not merely demonstrate it.

---

# 15. Scenario Runner

Build one deterministic runner.

Required flow:

```text
load scenario
↓
reset world
↓
apply deterministic fault configuration
↓
start fresh conversation/run
↓
execute agent
↓
capture ReasonFuse events
↓
capture outcome
↓
normalize result
↓
evaluate
↓
persist raw + normalized record
```

Every repetition must start from a clean scenario state.

---

# 16. Repetition Strategy

Use:

```text
num_repetitions = 1
```

where supported by the evaluation path.

If `evaluate_agent()` is practical with the selected package versions, use it.

Otherwise implement equivalent explicit repetition in the runner while preserving the same semantics.

Do not claim Foundry `evaluate_agent()` usage if it was not actually used.

---

# 17. Run Result Schema

Each run should persist:

```text
scenario_id
repetition

run_id
conversation_id
agent_session_id

category
expected_failure_type
actual_failure_type

expected_trip
actual_trip

expected_useful_recheck
actual_useful_recheck

expected_outcome
actual_outcome

healthy_completion_expected
healthy_completion_actual

steps
tool_calls
side_effects

containment_step
containment_latency_ms

objective_progress_events
stall_events

tokens_in optional
tokens_out optional
estimated_cost optional

trace_id
agent_version
model_version
prompt_version
toolbox_version
knowledge_base_version
reasonfuse_contract_version

timestamp
```

---

# 18. LocalEvaluator

Implement deterministic evaluation.

Required comparisons:

```text
expected_trip vs actual_trip
expected_failure_type vs actual_failure_type
expected_useful_recheck vs actual_useful_recheck
expected_outcome vs actual_outcome
healthy_completion_expected vs actual
```

Do not use an LLM evaluator for these ground-truth checks.

---

# 19. Confusion Matrix

For binary containment evaluation:

```text
Positive
= scenario should be contained

Negative
= healthy scenario should not be contained
```

Compute:

```text
TP
FP
TN
FN
```

Then:

```text
Recall
Precision
False Positive Rate
False Negative Rate
Accuracy optional
F1 optional
```

Do not hide raw counts.

---

# 20. Category-Level Metrics

Report per category:

```text
Exact Loop Recall
Oscillation Recall
Retrieval Churn Recall
Outcome Failure Detection Rate
Healthy Completion Rate
Useful Recheck Preservation Rate
```

Also report overall metrics.

---

# 21. Required Core Metrics

At minimum calculate:

```text
Recall
Precision
FPR
FNR

Healthy Completion Rate

Useful Recheck Preservation Rate

Postcondition Failure Detection Rate

Containment Rate

Containment Latency
  p50
  p95
  p99 if sample size supports it

Tool Calls / Run

Redundant Tool Calls / Run if derivable

Steps / Run

Tokens / Run where available

Cost / Run where available
```

If token/cost data is unavailable, mark:

```text
NOT AVAILABLE
```

Do not invent estimates.

---

# 22. OFF / ON Impact Comparison

Run a controlled OFF/ON subset.

Use the same:

```text
scenario
prompt
model
tools
world state
versions
```

Only change:

```text
ReasonFuse enabled
```

Recommended subset:

```text
5 Exact Loop
5 Oscillation
5 Retrieval Churn
5 Outcome / stalled scenarios if meaningful
```

At minimum compare:

```text
tool calls
steps
runtime
tokens if available
containment
outcome
```

Goal:

```text
show measured waste reduction
```

Do not claim causal impact if inputs differ materially.

---

# 23. 10,000-Event Microbenchmark

Implement a no-network, no-LLM microbenchmark for ReasonFuse core event processing.

Generate:

```text
10,000 trajectory events
```

Exercise:

```text
fingerprinting
progress delta evaluation
loop window
oscillation window
retrieval churn state
Run Contract counters
fuse decisions
```

Measure:

```text
total runtime
throughput events/sec
latency p50
latency p95
latency p99
peak/approx memory if practical
```

Do not compare this directly to full agent latency.

It measures only ReasonFuse core overhead.

---

# 24. Reproducibility Controls

Every benchmark run should record:

```text
git commit
dataset version
run_contract_version
agent version
model version
prompt version
toolbox version
knowledge_base_version
dependency versions
Azure region
date/time
```

Stable/Candidate release comparison is Phase 4.

Phase 3 should focus on one frozen benchmark candidate unless explicitly running OFF/ON.

---

# 25. Reset Integrity

Implement and test scenario reset.

A run must not inherit:

```text
previous service state
previous counters
previous approval
previous conversation
previous AgentSession state
previous retrieval cache affecting evidence
```

Add explicit reset assertions.

A benchmark with state leakage is invalid.

---

# 26. Failure Handling

Classify runner failures separately from ReasonFuse outcomes.

Example:

```text
RUNNER_ERROR
ENVIRONMENT_ERROR
MODEL_ERROR
TOOL_ERROR
TIMEOUT
SCENARIO_RESET_ERROR
```

Do not count infrastructure errors as false negatives or true positives.

Report excluded/invalid runs separately.

---

# 27. Raw Results

Preserve raw machine-readable output.

Recommended:

```text
JSONL
```

Example:

```text
benchmark/reports/raw/run_2026xxxx.jsonl
```

Never overwrite the only raw result file.

---

# 28. Normalized Results

Generate normalized CSV/JSON suitable for:

```text
confusion matrix
category metrics
OFF/ON comparison
charts
submission evidence
```

---

# 29. Charts

Generate only useful charts.

Recommended:

```text
Confusion Matrix
Detection Rate by Category
Healthy Preservation
Useful Recheck Preservation
Containment Latency Distribution
OFF vs ON Tool Calls
OFF vs ON Steps
Microbenchmark Latency
```

Do not spend Phase 3 on visual polish.

Phase 4 will handle presentation.

---

# 30. Acceptance Threshold Policy

Do not secretly choose thresholds after seeing all benchmark results.

Before the full 15-run competition benchmark:

```text
freeze detector thresholds
freeze Run Contract
record configuration
```

If tuning is necessary:

```text
use a clearly separated tuning subset
then freeze
then run final evaluation set
```

Do not tune on the final test results and report them as unbiased evidence.

---

# 31. Preferred Train/Tune/Test Discipline

Do not claim a statistical train/tune/test split from this 15-scenario
competition profile. Use the Phase 2-frozen thresholds and, if exploratory
tuning is needed, complete it before the final profile run. At minimum:

```text
freeze thresholds before the final 15-run evidence run
```

and document this limitation.

---

# 32. Phase 3 Scripts

Create:

```text
scripts/run_phase3_benchmark.ps1
scripts/run_phase3_microbenchmark.ps1
scripts/generate_phase3_report.ps1
```

Main benchmark script should:

```text
preflight
verify Phase 2 PASS
verify dataset schema
freeze/record versions
run scenarios
capture raw outputs
evaluate
generate metrics
fail loudly on invalid run count
```

The scripts must work from the repository root on Windows PowerShell. Python
helpers may be used for dataset validation, execution, normalization and
metrics. Do not make a shell-only `.sh` entry point the only reproducible path.
Every external/hosted command must be wrapped by
`scripts/verification_command.py`; local deterministic commands must still
write a machine-readable result and exit non-zero on invalid evidence.

---

# 33. Benchmark Completion Gate

The main evidence run is complete only if:

```text
15 valid runs
```

or, if external failure prevents this:

```text
exact valid count reported
invalid runs separately reported
reason documented
```

Do not silently replace missing runs.

---

# 34. PHASE3_REPORT.md

Create:

```text
# Phase 3 Evidence & Benchmark Report

## Environment
...

## Dataset
Version:
Scenario count:
Category counts:

## Run Summary
Expected runs: 15
Valid runs:
Invalid runs:
Failure reasons:

## Confusion Matrix
TP:
FP:
TN:
FN:

## Overall Metrics
Recall:
Precision:
FPR:
FNR:
Healthy Completion:
Useful Recheck Preservation:
Postcondition Failure Detection:
Containment Rate:

## Category Metrics
Exact Loop:
Oscillation:
Retrieval Churn:
Outcome Failure:
Healthy:

## Containment Performance
p50:
p95:
p99:

## OFF / ON Impact
Tool Calls:
Steps:
Runtime:
Tokens:
Cost:

## 10,000-Event Microbenchmark
Throughput:
p50:
p95:
p99:
Memory:

## Limitations
...

## Architecture Change Required?
YES / NO

## Phase 3 Result
PASS / BLOCKED
```

---

# 35. What Phase 3 Must NOT Do

Do not spend Phase 3 on:

```text
APIM stable/candidate rollout
Judge Mode final UI
automatic rollback
video editing
usability study
new ReasonFuse detectors
multi-agent features
new Azure services
major prompt redesign
architecture redesign
```

If the benchmark exposes a detector bug:

```text
fix detector implementation
rerun affected tests
rerun final benchmark
```

Do not expand product scope.

---

# 36. Construction Completion Criteria

Construction is complete when:

```text
[ ] versioned 15-scenario dataset exists
[ ] schema validates all scenarios
[ ] category counts are exactly 3 each
[ ] deterministic runner exists
[ ] reset integrity checks exist
[ ] 1-repetition competition execution is implemented
[ ] raw result persistence exists
[ ] normalized result pipeline exists
[ ] LocalEvaluator exists
[ ] confusion matrix code exists
[ ] core metric calculations exist
[ ] OFF/ON controlled subset exists
[ ] 10,000-event microbenchmark exists
[ ] report generator exists
[ ] PHASE3_REPORT.md template exists
[ ] Phase 2 reports remain unchanged; deleted evidence indexes are not recreated
[ ] raw/normalized artifacts can be indexed in a disposable temporary batch
[ ] fixture-based findings are explicit
```

At the end of construction, state:

```text
PHASE 3 CONSTRUCTION COMPLETE
READY FOR INDEPENDENT VALIDATION
```

Do not self-award Phase 3 PASS.
