# Phase 3 Evidence Benchmark — Independent Verification Report

## Scope

The active benchmark is now the bounded Microsoft Agentathon profile:

| Category | Scenarios |
| --- | ---: |
| Healthy | 3 |
| Exact Loop | 3 |
| Oscillation | 3 |
| Retrieval Churn | 3 |
| Outcome Failure | 3 |
| **Total** | **15** |

Each scenario is executed once by default. This single-pass profile matches the
competition goal and keeps the project within its budget.

Execution profile: **15 scenarios × 1 repetition = 15 runs**.

## Verification result

The 15-scenario deterministic suite was executed locally in a disposable run
directory and independently checked before that directory was removed.

| Gate | Result | Detail |
| --- | --- | --- |
| Dataset count | PASS | 15 unique records, 3 per category |
| Runner integrity | PASS | 15 valid records, no runner errors |
| Ground truth | PASS | Expected and actual classifications matched |
| Confusion matrix | PASS | TP 12, FP 0, TN 3, FN 0 |
| Core metrics | PASS | Recall, precision, FPR, FNR and accuracy recomputed |
| Healthy preservation | PASS | 3/3 healthy cases completed without containment |
| OFF/ON comparison | PASS | 15 controlled pairs |
| Microbenchmark | PASS | 10,000 local events, network disabled |

Bounded Phase 3 result: **PASS for the local 15-scenario Agentathon profile**.
This does not claim production or hosted-platform verification.

## Reproducibility

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset
.venv/Scripts/python.exe -m benchmark.runners.run_suite `
  --dataset benchmark/datasets/reasonfuse_v2.jsonl `
  --output-dir <temporary-run-dir> `
  --repetitions 1 `
  --include-impact
.venv/Scripts/python.exe -m benchmark.microbenchmark.run_microbenchmark `
  --output <temporary-run-dir>/microbenchmark.json
```

Raw execution artifacts are intentionally temporary. The report records the
result; a later rerun can recreate the artifacts locally when needed.

## Explicit boundaries

The following remain outside this bounded competition verification:

- cloud deployment and provider calls

They are outside the local 15-scenario Agentathon profile.
