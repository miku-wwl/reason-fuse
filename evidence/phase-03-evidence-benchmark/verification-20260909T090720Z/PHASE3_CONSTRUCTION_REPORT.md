# Phase 3 Evidence Benchmark — Construction Report

> This is a construction-layer report. It records executed local evidence; it does not self-award the independent Phase 3 verification result.

## Scope and result

- Batch: `verification-20260909T090720Z`
- Dataset: `D:/workshop/sep/reason-fuse/benchmark/datasets/reasonfuse_v1.jsonl`
- Dataset SHA-256: `87d7d9db77dc8ce346e4bd95d3e8b06b07744c81df9726daabae03a8dbf7cd29`
- Runs: `300` / expected `300`
- Valid runner records: `300`; invalid: `0`
- LocalEvaluator-correct records: `300`
- Execution layer: `local deterministic ReasonFuse engine; no network, LLM, Azure, or hosted Operations backend`

Construction status: `COMPLETE — local deterministic evidence materialized`.
Independent verification status: `NOT RUN by this construction command`.

## Confusion matrix and overall metrics

| Metric | Value |
| --- | ---: |
| TP | 240 |
| FP | 0 |
| TN | 60 |
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
| Exact Loop | 60 | 60 | 1 | 1 |
| Healthy | 60 | 60 | 0 | 0 |
| Oscillation | 60 | 60 | 1 | 1 |
| Outcome Failure | 60 | 60 | 1 | 1 |
| Retrieval Churn | 60 | 60 | 1 | 1 |

- Postcondition failure detection: `60/60`.
- Successful postcondition verification: `12/12`.
- Useful recheck preservation: `12/12`.

## Work and latency

- Tool calls/run: `2.810000`.
- Redundant canonical calls/run: `0.750000`.
- Steps/run: `2.810000`.
- Containment latency p50/p95/p99 ms: `0.484550` / `0.993975` / `1.485562`.
- Tokens/run: `NOT AVAILABLE` (no LLM was invoked).
- Cost/run: `NOT AVAILABLE` (no billable provider was invoked).

## Controlled OFF/ON subset

- Paired runs: `20`.
- ON mean tool calls / steps: `2.950000` / `2.950000`.
- OFF mean tool calls / steps: `3.450000` / `3.450000`.
- OFF-minus-ON mean tool calls / steps: `0.500000` / `0.500000`.
- Control definition: same scenario, repetition, prompt, tool arguments, world state, and local engine; only reasonfuse_enabled differs.

## Microbenchmark

- Status: `PASS`; events: `10000`.
- Events/second: `5454.777630`.
- Per-event latency p50/p95/p99 ns: `73900.000000` / `501715.000000` / `792159.000000`.
- Peak traced memory: `580390` bytes.

## Evidence and boundaries

Raw evidence is in `raw/runs.jsonl`; normalized records are in `normalized/results.jsonl`; machine summaries are in `summary/`.

- FoundryEvals layer: `NOT_RUN` — FoundryEvals was not invoked; this construction uses the deterministic LocalEvaluator.
- Foundry IQ native retrieval: `NOT VERIFIED`.
- Production Operations backend: `NOT VERIFIED`.
- Cloud Core trace correlation: `NOT VERIFIED`.
- Concurrent/forked turns and cold-start recovery: `NOT VERIFIED`.
- Fixture reset: deterministic local reset is recorded per run; hosted/production isolation is not claimed.
- Architecture change required by this local construction: `NO`.

## Reproduction

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset
.venv/Scripts/python.exe -m benchmark.runners.run_suite --dataset benchmark/datasets/reasonfuse_v1.jsonl --output-dir <run-dir> --repetitions 3 --include-impact
.venv/Scripts/python.exe -m benchmark.microbenchmark.run_microbenchmark --output <run-dir>/microbenchmark.json
```

Source commit recorded by runner: `283bc6cfdfe9482b5846b61d1555a2ac09809931`.
