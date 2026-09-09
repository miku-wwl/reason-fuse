# ReasonFuse Phase 3 Agentathon dataset

`reasonfuse_v2.jsonl` is the active 15-scenario competition dataset:

Execution profile: **15 scenarios × 1 repetition = 15 runs**.

| Category | IDs | Count |
| --- | --- | ---: |
| Healthy | H-001, H-007, H-018 | 3 |
| Exact Loop | EL-001, EL-005, EL-013 | 3 |
| Oscillation | OS-001, OS-007, OS-018 | 3 |
| Retrieval Churn | RC-001, RC-010, RC-020 | 3 |
| Outcome Failure | OF-001, OF-002, OF-015 | 3 |
| **Total** | | **15** |

The actions are deterministic inputs to the local ReasonFuse engine. They are
not transcripts of an LLM and do not claim Hosted, Foundry IQ, or production
Operations coverage. The 15 records are a curated Agentathon profile, not a
statistical production regression suite.

Validate it from the repository root with:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m benchmark.datasets.validate_dataset
```

Detector thresholds and the contract freeze used by the 15-scenario profile are
recorded in `frozen_thresholds.json`.
