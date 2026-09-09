# ReasonFuse Phase 3 dataset

`reasonfuse_v1.jsonl` is the frozen 100-scenario construction dataset:

| Category | IDs | Count |
| --- | --- | ---: |
| Healthy | H-001..H-020 | 20 |
| Exact Loop | EL-001..EL-020 | 20 |
| Oscillation | OS-001..OS-020 | 20 |
| Retrieval Churn | RC-001..RC-020 | 20 |
| Outcome Failure | OF-001..OF-020 | 20 |

The actions are deterministic inputs to the local ReasonFuse engine. They are
not transcripts of an LLM and do not claim Hosted, Foundry IQ, or production
Operations coverage. The dataset intentionally records the exact fixture and
contract version so the LocalEvaluator can recompute the ground truth.

Validate it from the repository root with:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset
```

Detector thresholds and the contract freeze used before the 300-run execution
are recorded in `frozen_thresholds.json`.
