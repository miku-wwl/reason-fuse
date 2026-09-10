# Phase 3 Evidence Benchmark — Construction Report

> This is a construction-layer report. It records executed local evidence; it does not self-award the independent Phase 3 verification result.

## Scope and result

- Batch: `cleanup-15x1`
- Dataset: `D:/workshop/sep/reason-fuse/benchmark/datasets/reasonfuse_v2.jsonl`
- Dataset SHA-256: `cc3456ea76f20c94b749b2e0cdde7445e8a2497bf008de5a5a4451b4735d3d6c`
- Frozen thresholds SHA-256: `e08679ded3114754c2f0f0622f5733699220bb29cd1fec203a2f8d031ed24b20`.
- Execution profile: `15 scenarios × 1 repetition = 15 runs`.
- Runs: `15` / expected `15`
- Valid runner records: `15`; invalid: `0`
- LocalEvaluator-correct records: `15`
- Execution layer: `local deterministic ReasonFuse engine; no network, LLM, Azure, or hosted Operations backend`

Construction status: `COMPLETE — local deterministic evidence materialized`.
Independent verification status: `NOT RUN by this construction command`.

## Confusion matrix and overall metrics

| Metric | Value |
| --- | ---: |
| TP | 12 |
| FP | 0 |
| TN | 3 |
| FN | 0 |
| Recall | 1.000000 |
| Precision | 1.000000 |
| FPR | 0.000000 |
| FNR | 0.000000 |
| Accuracy | 1.000000 |
| F1 | 1.000000 |

## Category metrics

| Category | Runs | Correct | Expected trip rate | Actual trip rate |
| --- | ---: | ---: | ---: | ---: |
| Exact Loop | 3 | 3 | 1 | 1 |
| Healthy | 3 | 3 | 0 | 0 |
| Oscillation | 3 | 3 | 1 | 1 |
| Outcome Failure | 3 | 3 | 1 | 1 |
| Retrieval Churn | 3 | 3 | 1 | 1 |

- Postcondition failure detection: `3/3`.
- Successful postcondition verification: `1/1`.
- Useful recheck preservation: `1/1`.

## Work and latency

- Tool calls/run: `2.933333`.
- Redundant canonical calls/run: `0.666667`.
- Steps/run: `2.933333`.
- Containment latency p50/p95/p99 ms: `0.542000` / `1.296800` / `1.326480`.
- Tokens/run: `NOT AVAILABLE` (no LLM was invoked).
- Cost/run: `NOT AVAILABLE` (no billable provider was invoked).

## Controlled OFF/ON subset

- Paired runs: `15`.
- ON mean tool calls / steps: `2.933333` / `2.933333`.
- OFF mean tool calls / steps: `3.333333` / `3.333333`.
- OFF-minus-ON mean tool calls / steps: `0.400000` / `0.400000`.
- Control definition: same scenario, repetition, prompt, tool arguments, world state, and local engine; only reasonfuse_enabled differs.

## Microbenchmark

- Status: `PASS`; events: `10000`.
- Events/second: `5273.438880`.
- Per-event latency p50/p95/p99 ns: `77700.000000` / `521045.000000` / `798821.000000`.
- Peak traced memory: `580390` bytes.

## Evidence and boundaries

Raw evidence is in `raw/runs.jsonl`; normalized records are in `normalized/results.jsonl`; machine summaries are in `summary/`.

- Fixture reset: deterministic local reset is recorded per run.
- Hosted deployment is not part of this local benchmark run.
- Architecture change required by this local construction: `NO`.

## Phase 3 Result

`NOT AWARDED BY CONSTRUCTION — READY FOR INDEPENDENT VALIDATION`.

## Reproduction

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset
.venv/Scripts/python.exe -m benchmark.runners.run_suite --dataset benchmark/datasets/reasonfuse_v2.jsonl --output-dir <run-dir> --repetitions 1 --include-impact
.venv/Scripts/python.exe -m benchmark.microbenchmark.run_microbenchmark --output <run-dir>/microbenchmark.json
```

Source commit recorded by runner: `7b51c98430a5c8b4042b74c709270f6f71618ed9`.
