# ReasonFuse Phase 3 — Evidence & Benchmark Verification Prompt

> **Purpose:** Independently verify that the Phase 3 benchmark is valid, reproducible, statistically honest, and sufficient to support ReasonFuse competition claims.  
> **Audience:** GPT-6 Astra / independent validation agent  
> **Phase:** 3 — Evidence & Benchmark  
> **Role:** Validator, not benchmark author  
> **Prerequisite:** Phase 2 = PASS  
> **Primary Exit Gate:** `15 valid competition scenarios + trustworthy metrics + confusion matrix + reproducibility`

---

# 0. Current Construction Handoff

The Phase 3 benchmark construction has been materialized in the repository.
Use this handoff as the starting point for independent verification; do not
silently replace it with a new benchmark design.

Canonical construction inputs:

```text
benchmark/datasets/reasonfuse_v2.jsonl
benchmark/datasets/schema.json
benchmark/datasets/frozen_thresholds.json
benchmark/datasets/generate_dataset_v2.py
```

Canonical runner/evaluator entry points:

```text
benchmark/runners/reset_scenario.py
benchmark/runners/run_single.py
benchmark/runners/run_suite.py
benchmark/evaluators/local_evaluator.py
benchmark/evaluators/confusion_matrix.py
benchmark/evaluators/impact_metrics.py
benchmark/evaluators/foundry_evals.py
benchmark/microbenchmark/run_microbenchmark.py
```

The reproducible Windows entry point is:

```powershell
Set-Location D:\workshop\sep\reason-fuse
$env:PYTHONPATH = 'src'
.\scripts\run_phase3_benchmark.ps1 -Repetitions 1 -IncludeImpact
```

The construction script writes raw artifacts to a disposable system-temporary
directory. The exact batch path is printed as `PHASE3_CONSTRUCTION_COMPLETE`
when the script finishes; do not assume a retained repository evidence path.
The retained review report is:

```text
benchmark/PHASE3_REPORT.md
```

For a fresh run, use the printed temporary batch path for raw artifacts and
command captures. A typical layout is:

```text
%TEMP%/reasonfuse-phase3/verification-<UTC>/
%TEMP%/reasonfuse-phase3/commands/verification-<UTC>/
```

The batch contains:

```text
raw/runs.jsonl                         15 ON records
raw/off_on.jsonl                       controlled OFF/ON subset
normalized/results.jsonl               evaluated normalized records
summary/metrics.json                   recomputable metrics
summary/off_on_impact.json             paired impact metrics
summary/foundry_evals.json             Foundry compatibility status
microbenchmark.json                    10,000-event result
PHASE3_REPORT.md                       batch report
index.json                             SHA-256 artifact index
```

The repository-level report is:

```text
benchmark/PHASE3_REPORT.md
```

The construction report records `PHASE3_CONSTRUCTION_COMPLETE`; it does not
award `PHASE 3 RESULT: PASS`. The validator must independently recompute the
result from raw evidence.

---

# 0.1 Phase Boundary

This verification validates the frozen Phase 2 ReasonFuse core through a
deterministic local benchmark. The benchmark runner is intentionally:

```text
no network
no Azure calls
no LLM invocation
no hosted Operations backend
no Foundry IQ native retrieval
no cloud trace query
```

The following remain explicit boundaries and are not required to be silently
promoted to Phase 3 PASS claims:

```text
Foundry IQ native retrieval                 NOT VERIFIED
production Operations restart/health        NOT VERIFIED
cloud Core trace correlation                NOT VERIFIED
concurrent/forked turns                     NOT VERIFIED
cold-start recovery                         NOT VERIFIED
```

These boundaries require a later production/integration evidence path. Do not
block the deterministic Phase 3 benchmark solely because one of these is not
verified. Do not report them as verified because the local fixture passed.

FoundryEvals is different: it is an optional Phase 3 quality layer. Attempt it
if the pinned environment supports it. If it is unavailable or incompatible,
record the exact limitation and use the documented `PARTIAL`/exception path;
never claim that an unavailable evaluator ran.

---

# 1. Mission

Your job is not to generate attractive numbers.

Your job is to determine whether the evidence is trustworthy.

You must independently validate:

```text
dataset quality
scenario diversity
ground truth
reset integrity
run count
metric correctness
false-positive handling
OFF/ON fairness
Foundry evaluation usage
microbenchmark correctness
reproducibility
```

Return:

```text
Dataset Quality          PASS / FAIL
Runner Integrity         PASS / FAIL
15-Scenario Completion   PASS / FAIL
Ground Truth             PASS / FAIL
Confusion Matrix         PASS / FAIL
Core Metrics             PASS / FAIL
Healthy Preservation     PASS / FAIL
OFF/ON Comparison        PASS / FAIL
FoundryEvals Layer       PASS / PARTIAL / FAIL
Microbenchmark           PASS / FAIL
Reproducibility          PASS / FAIL

PHASE 3 RESULT:
PASS / BLOCKED
```

---

# 2. Validation Principles

## Principle 1 — Do Not Trust Summary Reports Alone

Recompute important metrics from raw records.

Do not accept:

```text
README claims
generated charts
hand-entered totals
```

without checking the underlying run data.

---

## Principle 2 — Do Not Reward Easy Benchmarks

A benchmark where every failure scenario is an obvious repeated call is insufficient.

Inspect scenario diversity.

Healthy cases must challenge false-positive behavior.

---

## Principle 3 — Invalid Runs Are Not Predictions

Do not classify:

```text
timeout
SDK error
deployment failure
reset failure
tool outage
```

as TP/FP/TN/FN.

Invalid runs must be reported separately.

---

## Principle 4 — No Hidden Threshold Tuning

Determine whether detector thresholds were changed after observing the final benchmark outcomes.

If yes:

```text
mark evaluation leakage
```

and require a clean rerun after freezing thresholds.

---

# 3. Pre-Validation Audit

Record:

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
region
benchmark date/time
```

Confirm:

```text
docs/phases/phase-02-core/verification-report.md
→ contains INDEPENDENT_PHASE2_VALIDATION_PASS
```

Do not rerun the Phase 2 hosted campaign as part of this prompt. Verify the
report handoff and keep Phase 2 reports unchanged. The deleted Phase 2
evidence indexes are not prerequisites for this local Phase 3 verification.

Run Phase 3 preflight:

```powershell
Set-Location D:\workshop\sep\reason-fuse
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset
.tools/check-phase2-artifacts.ps1
```

Then verify the fresh temporary batch `index.json`, its listed SHA-256 hashes,
the command-capture `RESULT` records, and the clean working-tree diff scope.
The preflight must not substitute a summary-only PASS for these checks. Do not
commit the temporary raw artifacts.

---

# 4. Dataset Count Validation

Inspect the dataset.

Required exact counts:

```text
Healthy Investigations   3
Exact Loop               3
Oscillation              3
Retrieval Churn          3
Outcome Failure          3
--------------------------------
Total                   15
```

Confirm unique scenario IDs.

Required ranges:

```text
H-001, H-007, H-018
EL-001, EL-005, EL-013
OS-001, OS-007, OS-018
RC-001, RC-010, RC-020
OF-001, OF-002, OF-015
```

Equivalent unique naming is acceptable, but duplicates are not.

---

# 5. Schema Validation

Validate all 15 records against the declared schema.

At minimum each must have:

```text
scenario_id
category
description
initial_world_state
fault_configuration
user_prompt
expected result
run_contract_version
```

The declared schema also permits deterministic `actions`. For every action,
inspect at least:

```text
type
tool_name
arguments
result
side_effect
approved
```

If `verify_postcondition` is present, confirm that the action is the intended
fresh verification read for the accepted side effect. Validate the actual file
with:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset --dataset benchmark/datasets/reasonfuse_v2.jsonl
```

Reject silently malformed or incomplete scenarios.

---

# 6. Scenario Diversity Audit

For each category, inspect all 3 cases.

Determine whether they vary meaningful dimensions.

Flag benchmark inflation such as:

```text
same scenario
same tool sequence
same fault
only service name changed
```

A few variants are acceptable, but a category cannot be superficial clones.

Produce a short diversity assessment per category.

---

# 7. Healthy Scenario Audit

Healthy scenarios are the main false-positive defense.

Confirm they include non-trivial patterns such as:

```text
useful recheck after side effect
same tool after world-state change
repeated retrieval with genuinely new evidence
repeated A/B pattern with new evidence
unknown correct path with objective progress
same operation with meaningfully different args
```

If Healthy scenarios are trivial:

```text
Healthy Preservation = FAIL
```

even if reported FPR is low.

---

# 8. Ground-Truth Audit

Inspect expected labels.

Confirm:

```text
Healthy
→ should_trip = false

Exact Loop
→ expected_failure_type = EXACT_LOOP

Oscillation
→ expected_failure_type = OSCILLATING

Retrieval Churn
→ expected_failure_type = RETRIEVAL_CHURN

Outcome Failure
→ expected_outcome = POSTCONDITION_FAILED
```

For this frozen dataset, `expected_useful_recheck = true` means a bounded
recheck actually verifies the accepted side effect and produces
`OUTCOME_VERIFIED`. An unhealthy or degraded fresh recheck is an outcome
failure, not a preserved useful recheck. Confirm this interpretation from the
raw action and outcome records rather than accepting a label in isolation.

Do not assume all Outcome Failure cases must necessarily trip the Behavioral Fuse if the intended architecture distinguishes outcome verification from behavioral containment.

Evaluate expected labels according to the frozen ReasonFuse semantics.

---

# 9. Reset Integrity Validation

Select representative scenarios from all five categories.

Run:

```text
scenario A
reset
scenario B
reset
scenario A again
```

Confirm no state leakage.

Inspect:

```text
world state
execution counters
conversation IDs
retrieval state/cache behavior
```

The current Phase 3 runner is a local deterministic fixture. Its authoritative
reset assertions are:

```text
reset.reset = RESET_COMPLETE
reset.network = DISABLED
reset.fixture_scope = true
reset.counters.steps/tool_calls/side_effects = 0
reset.conversation_id changes by scenario/repetition/mode
```

Do not require a hosted AgentSession or real approval state from this local
benchmark and then call the benchmark invalid; those are Phase 4/production
integration concerns. Do confirm that no in-process ReasonFuse state, pending
postcondition, retrieval attempt, or fuse counter leaks across repetitions.

Required:

```text
fresh scenario starts clean
```

If state leakage affects results:

```text
Runner Integrity = FAIL
```

---

# 10. Repetition Validation

Confirm each scenario has exactly:

```text
1 valid competition repetition
```

Expected:

```text
15 × 1 = 15 valid runs
```

Check raw records, not summary totals.

Verify no duplicate run record was counted twice.

---

# 11. Valid vs Invalid Run Audit

Count separately:

```text
valid runs
invalid runs
```

Inspect all invalid runs.

Classify:

```text
RUNNER_ERROR
ENVIRONMENT_ERROR
MODEL_ERROR
TOOL_ERROR
TIMEOUT
SCENARIO_RESET_ERROR
OTHER
```

Invalid runs must not appear in confusion matrix counts.

---

# 12. 15-Scenario Completion Gate

PASS only when:

```text
valid runs = 15
```

If valid runs < 15:

```text
15-Scenario Completion = FAIL
```

unless the phase definition was explicitly amended before execution.

Do not round or extrapolate.

---

# 13. Raw Evidence Integrity

Confirm each valid run contains enough fields to reconstruct evaluation:

```text
scenario_id
repetition
expected label
actual label
trip/no-trip
outcome
useful recheck
tool calls
steps
containment timing
version lineage
```

The current normalized records also expose the Phase 3 run-result fields as
flat keys, including:

```text
expected_failure_type / actual_failure_type
expected_trip / actual_trip
expected_useful_recheck / actual_useful_recheck
expected_outcome / actual_outcome
healthy_completion_expected / healthy_completion_actual
steps / tool_calls / side_effects
containment_step / containment_latency_ms
objective_progress_events / stall_events
tokens_in / tokens_out / estimated_cost
trace_id
agent_version / model_version / prompt_version
toolbox_version / knowledge_base_version
reasonfuse_contract_version
timestamp
```

`tokens_*` and `estimated_cost` are expected to be `NOT AVAILABLE` because the
construction path invokes no model or billable provider. `trace_id` is
`NOT_AVAILABLE_LOCAL`; this is not cloud trace evidence.

If metrics cannot be independently recomputed:

```text
Core Metrics = FAIL
```

---

# 14. Confusion Matrix Recalculation

From raw valid records, independently recompute:

```text
TP
FP
TN
FN
```

Binary definition:

```text
Positive:
scenario expected runtime containment

Negative:
healthy scenario expected not to be contained
```

Be careful with Outcome Failure scenarios.

Use the benchmark's declared evaluation semantics consistently.

Recompute:

```text
Recall = TP / (TP + FN)
Precision = TP / (TP + FP)
FPR = FP / (FP + TN)
FNR = FN / (FN + TP)
```

Compare with generated report.

Any unexplained mismatch:

```text
Confusion Matrix = FAIL
```

---

# 15. Category Recall Validation

Independently calculate:

```text
Exact Loop detection rate
Oscillation detection rate
Retrieval Churn detection rate
Postcondition Failure Detection Rate
Healthy Completion Rate
Useful Recheck Preservation Rate
```

Check denominators carefully.

Do not allow invalid runs to reduce or inflate denominators silently.

---

# 16. Useful Recheck Preservation Audit

Inspect all scenarios labeled:

```text
expected_useful_recheck = true
```

Verify ReasonFuse preserved them.

Inspect at least several raw traces.

Confirm that a "preserved" recheck occurred after meaningful state change or required postcondition verification.

Do not accept a mislabeled repeated call as useful merely because the benchmark says so.

---

# 17. Todo-Only Progress Audit

Find scenarios where planning/Todo state changes without objective evidence.

Confirm:

```text
Todo Delta > 0
Objective Progress = false
```

If Todo Delta resets no-progress counters:

```text
Ground Truth / Core Logic Evidence = FAIL
```

This is a frozen correctness invariant.

---

# 18. Outcome Failure Audit

Inspect all Outcome Failure runs.

Required architecture semantics:

```text
tool/action accepted
≠
outcome success
```

Confirm:

```text
accepted action
→ postcondition check
→ POSTCONDITION_FAILED
```

Do not accept model prose as verification.

---

# 19. Containment Latency Validation

Recompute containment latency from raw timestamps where possible.

Validate:

```text
p50
p95
p99 if reported
```

Check units.

For the current local runner, `containment_latency_ms` is measured with
`time.perf_counter()` around the deterministic dispatch/record path. The raw
record does not claim a distributed wall-clock or hosted network timestamp.
Verify that methodology and units; do not report it as Azure, model, APIM, or
production latency.

Do not report network/runtime latency as ReasonFuse core processing latency.

Full-run containment latency and microbenchmark event latency are separate metrics.

---

# 20. Tool-Call / Step Metrics Audit

Recompute:

```text
Tool Calls / Run
Steps / Run
Redundant Tool Calls / Run
```

where reported.

Inspect definitions.

A metric must have a documented calculation.

---

# 21. Token / Cost Audit

If token or cost metrics are reported:

```text
verify source
verify units
verify aggregation
```

If data was unavailable, the correct value is:

```text
NOT AVAILABLE
```

Do not allow invented estimates into the final report.

---

# 22. OFF / ON Fairness Audit

Inspect the controlled OFF/ON subset.

Confirm paired runs preserve:

```text
same scenario
same prompt
same model
same tools
same world state
same versions
```

Only intended variable:

```text
ReasonFuse enabled / disabled
```

If model stochasticity materially affects comparability, require:

```text
multiple repetitions
```

and report uncertainty rather than a single anecdote. The current OFF/ON
subset is local and deterministic: 5 Exact Loop, 5 Oscillation, 5 Retrieval
Churn, and 5 Outcome Failure scenarios, one paired repetition each. Confirm
that only `reasonfuse_enabled` differs and do not present this 15-pair fixture
comparison as a production causal estimate.

---

# 23. OFF / ON Impact Recalculation

For the paired subset, recompute:

```text
tool calls
steps
runtime
tokens if available
cost if available
containment rate
```

Check whether ReasonFuse actually reduces waste.

Do not require every metric to improve in every run.

Require the reported aggregate claim to match raw evidence.

---

# 24. FoundryEvals Validation

Confirm which Foundry evaluators actually ran.

Record:

```text
evaluator name
version/API
scenario subset
valid results
```

Preferred:

```text
Task Navigation Efficiency
Tool Call Accuracy
Tool Selection Accuracy
Tool Input Accuracy
Tool Output Utilization
Tool Call Success
Task Completion / Task Adherence where useful
```

If only a subset works:

```text
FoundryEvals Layer = PARTIAL
```

This does not automatically block Phase 3 if deterministic ReasonFuse evaluation is complete.

Do not claim unavailable evaluators were used.

The current construction compatibility artifact is:

```text
summary/foundry_evals.json
status = NOT_RUN
boundary = NOT VERIFIED
```

This is an explicit compatibility result, not a hidden FoundryEvals PASS.
Independently check whether the pinned environment can run a real evaluator;
if it cannot, preserve the exact `NOT_RUN` reason in the validation report and
classify the layer as `PARTIAL` under the exception below.

---

# 25. Runtime vs Offline Evaluation Boundary

Confirm final report communicates:

```text
ReasonFuse
→ runtime progress containment

LocalEvaluator
→ deterministic benchmark correctness

FoundryEvals
→ offline agent trajectory quality
```

Do not make the false claim:

```text
Foundry cannot analyze trajectories
```

---

# 26. 10,000-Event Microbenchmark Validation

Run the microbenchmark independently.

Required:

```text
10,000 events
no network
no LLM
```

Confirm exercised logic includes representative core operations:

```text
fingerprinting
progress evaluation
loop detection
oscillation state
retrieval churn state
Run Contract counters
fuse decisions
```

Recompute or verify:

```text
total runtime
events/sec
p50
p95
p99
```

If memory is reported, verify methodology.

The construction output is in the fresh temporary batch directory printed by
the runner:

```text
<temporary-batch>/microbenchmark.json
```

The measurement loop creates isolated local engine packets and records 10,000
decision events. Reporting/indexing happens after the measured loop and must
not be counted as core event time. Treat the measured throughput as a local
ReasonFuse-core comparison point, not as full-agent or hosted latency.

---

# 27. Microbenchmark Isolation

Ensure the benchmark does not accidentally measure:

```text
network calls
Azure latency
LLM latency
disk-heavy reporting
sleep statements
```

The result should represent ReasonFuse core processing overhead.

---

# 28. Threshold Leakage Audit

Inspect git history/config timestamps if available.

Determine whether detector thresholds or Run Contract values changed after seeing the final benchmark results.

Inspect the frozen declaration:

```text
benchmark/datasets/frozen_thresholds.json
```

Compare its SHA-256 in `summary/dataset_metadata.json` with the actual file,
and compare the declared detector/contract values with the scenario overrides
and the ReasonFuse implementation. The final construction batch was generated
after this freeze; any later threshold edit requires a new evidence batch.

If yes:

```text
evaluation leakage = true
```

Required remediation:

```text
freeze thresholds
rerun final evaluation
```

Do not accept post-hoc threshold tuning as final unbiased evidence.

---

# 29. Reproducibility Test

From a clean state:

```text
run preflight
run a representative benchmark subset
regenerate metrics
```

At minimum include:

```text
2 Healthy
2 Exact Loop
2 Oscillation
2 Retrieval Churn
2 Outcome Failure
```

Compare classifications with the original run.

Small LLM-output differences may occur.

Core labels should remain stable.

---

# 30. Report Integrity

Inspect:

```text
benchmark/PHASE3_REPORT.md
```

If a fresh run was executed, compare its temporary batch report with the
repository report. The temporary batch is covered by its `index.json`; the
repository report is the retained review artifact.

Confirm every headline number can be traced to raw evidence.

Required report contents:

```text
dataset version
scenario counts
valid/invalid runs
confusion matrix
Recall
Precision
FPR
FNR
Healthy Completion
Useful Recheck Preservation
Postcondition Failure Detection
Containment metrics
OFF/ON impact
FoundryEvals status
microbenchmark
limitations
```

No unsupported marketing claim should appear as a measured result.

---

# 31. Failure Classification

Classify failures as:

```text
DATASET_DESIGN_ERROR
GROUND_TRUTH_ERROR
RESET_LEAKAGE
RUNNER_ERROR
METRIC_ERROR
EVALUATION_LEAKAGE
ENVIRONMENT_ERROR
FOUNDRY_EVAL_INCOMPATIBILITY
MICROBENCHMARK_ERROR
REASONFUSE_CORE_REGRESSION
ARCHITECTURE_ASSUMPTION_FAILURE
```

Do not reopen architecture for ordinary dataset or runner bugs.

---

# 32. Required Evidence Artifacts

Verify existence of:

```text
versioned dataset
raw run JSONL
normalized results
confusion matrix data
metrics summary
OFF/ON paired results
microbenchmark raw output
PHASE3_REPORT.md
SHA-256 evidence index
command-capture RESULT records
```

Charts are secondary.

Raw evidence is primary.

---

# 33. Phase 3 PASS Gate

Return:

```text
PHASE 3 RESULT: PASS
```

only when all mandatory conditions are true:

```text
[ ] exactly 15 curated scenarios exist

[ ] category counts are 3/3/3/3/3

[ ] scenario diversity is credible

[ ] Healthy scenarios meaningfully test false positives

[ ] reset integrity PASS

[ ] exactly 15 valid benchmark runs exist

[ ] raw results are sufficient to recompute metrics

[ ] confusion matrix independently matches report

[ ] Recall / Precision / FPR / FNR independently match report

[ ] Healthy Completion Rate verified

[ ] Useful Recheck Preservation Rate verified

[ ] Postcondition Failure Detection Rate verified

[ ] OFF/ON comparison is controlled and fair

[ ] no hidden threshold tuning contaminates final results

[ ] 10,000-event microbenchmark PASS

[ ] representative clean-state rerun reproduces classifications

[ ] no ReasonFuse Phase 2 core regression is discovered

[ ] no frozen architecture assumption fails
```

---

# 34. FoundryEvals Exception

FoundryEvals may be:

```text
PASS
or
PARTIAL
```

without blocking Phase 3, provided:

```text
deterministic LocalEvaluator
+
15-scenario evidence
+
core metrics
```

are fully valid.

If FoundryEvals is unavailable because of SDK/Preview limitations, document it exactly.

Do not redesign ReasonFuse.

---

# 35. BLOCKED Gate

Return:

```text
PHASE 3 RESULT: BLOCKED
```

if any competition-critical evidence condition fails, including:

```text
<15 valid runs
invalid confusion matrix
state leakage
trivial Healthy benchmark
unreproducible metrics
post-hoc threshold tuning without rerun
missing raw evidence
core detector regression
```

---

# 36. Final Validator Instruction

Phase 3 is the difference between:

```text
"We built a reliability layer."
```

and:

```text
"We ran 15 controlled executions and can show exactly
what it detects, what it preserves, and how quickly it contains failures."
```

Optimize for evidence quality, not impressive-looking percentages.

A lower but trustworthy metric is more valuable than a perfect number produced by a weak benchmark.
