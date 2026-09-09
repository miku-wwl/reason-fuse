# Phase 3 Evidence Benchmark — Construction Report

> This is a construction-layer report. It records executed local evidence; it does not self-award the independent Phase 3 verification result.

## Scope and result

- Batch: `verification-20260909T-v2-construction`
- Dataset: `D:/workshop/sep/reason-fuse/benchmark/datasets/reasonfuse_v2.jsonl`
- Dataset SHA-256: `75492a018b0b80f1ab15da00c41f5c7f3d4761fed29aa4d85c6938d5a2f7af94`
- Frozen thresholds SHA-256: `e08679ded3114754c2f0f0622f5733699220bb29cd1fec203a2f8d031ed24b20`.
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

- Tool calls/run: `2.720000`.
- Redundant canonical calls/run: `0.650000`.
- Steps/run: `2.720000`.
- Containment latency p50/p95/p99 ms: `0.432100` / `0.934210` / `1.270926`.
- Tokens/run: `NOT AVAILABLE` (no LLM was invoked).
- Cost/run: `NOT AVAILABLE` (no billable provider was invoked).

## Controlled OFF/ON subset

- Paired runs: `20`.
- ON mean tool calls / steps: `2.800000` / `2.800000`.
- OFF mean tool calls / steps: `3.300000` / `3.300000`.
- OFF-minus-ON mean tool calls / steps: `0.500000` / `0.500000`.
- Control definition: same scenario, repetition, prompt, tool arguments, world state, and local engine; only reasonfuse_enabled differs.

## Microbenchmark

- Status: `PASS`; events: `10000`.
- Events/second: `5310.110450`.
- Per-event latency p50/p95/p99 ns: `72000.000000` / `506135.000000` / `852015.000000`.
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

## Phase 3 Result

`NOT AWARDED BY CONSTRUCTION — READY FOR INDEPENDENT VALIDATION`.

## Reproduction

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset
.venv/Scripts/python.exe -m benchmark.runners.run_suite --dataset benchmark/datasets/reasonfuse_v2.jsonl --output-dir <run-dir> --repetitions 3 --include-impact
.venv/Scripts/python.exe -m benchmark.microbenchmark.run_microbenchmark --output <run-dir>/microbenchmark.json
```

Source commit recorded by runner: `6f16c64a9c0b5f2aa5d5c6fa72eaf09140847845`.
