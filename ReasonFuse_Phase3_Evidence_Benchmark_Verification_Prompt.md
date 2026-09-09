# ReasonFuse Phase 3 — Evidence & Benchmark Verification Prompt

> **Purpose:** Independently verify that the Phase 3 benchmark is valid, reproducible, statistically honest, and sufficient to support ReasonFuse competition claims.  
> **Audience:** GPT-6 Astra / independent validation agent  
> **Phase:** 3 — Evidence & Benchmark  
> **Role:** Validator, not benchmark author  
> **Prerequisite:** Phase 2 = PASS  
> **Primary Exit Gate:** `300 valid runs + trustworthy metrics + confusion matrix + reproducibility`

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
300-Run Completion       PASS / FAIL
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
PHASE2_REPORT.md
→ PASS
```

Run Phase 3 preflight.

---

# 4. Dataset Count Validation

Inspect the dataset.

Required exact counts:

```text
Healthy Investigations   20
Exact Loop               20
Oscillation              20
Retrieval Churn          20
Outcome Failure          20
--------------------------------
Total                   100
```

Confirm unique scenario IDs.

Required ranges:

```text
H-001 ... H-020
EL-001 ... EL-020
OS-001 ... OS-020
RC-001 ... RC-020
OF-001 ... OF-020
```

Equivalent unique naming is acceptable, but duplicates are not.

---

# 5. Schema Validation

Validate all 100 records against the declared schema.

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

Reject silently malformed or incomplete scenarios.

---

# 6. Scenario Diversity Audit

For each category, inspect all 20 cases.

Determine whether they vary meaningful dimensions.

Flag benchmark inflation such as:

```text
same scenario
same tool sequence
same fault
only service name changed
```

A few variants are acceptable, but a category cannot be 20 superficial clones.

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
AgentSession state
conversation IDs
approval state
retrieval state/cache behavior
```

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
3 valid repetitions
```

Expected:

```text
100 × 3 = 300 valid runs
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

# 12. 300-Run Completion Gate

PASS only when:

```text
valid runs = 300
```

If valid runs < 300:

```text
300-Run Completion = FAIL
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

and report uncertainty rather than a single anecdote.

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
PHASE3_REPORT.md
```

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
[ ] exactly 100 scenarios exist

[ ] category counts are 20/20/20/20/20

[ ] scenario diversity is credible

[ ] Healthy scenarios meaningfully test false positives

[ ] reset integrity PASS

[ ] exactly 300 valid benchmark runs exist

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
300-run evidence
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
<300 valid runs
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
"We ran 300 controlled executions and can show exactly
what it detects, what it preserves, and how quickly it contains failures."
```

Optimize for evidence quality, not impressive-looking percentages.

A lower but trustworthy metric is more valuable than a perfect number produced by a weak benchmark.
