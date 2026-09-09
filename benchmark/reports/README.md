# Phase 3 report pipeline

`generate_report.py` renders the batch-specific `PHASE3_REPORT.md` inside a
Phase 3 evidence directory. `index_artifacts.py` records SHA-256 hashes for
that batch. Raw and normalized JSONL are written to an explicitly chosen
temporary verification directory so each run is independent while it is being
checked. Raw run directories are disposable and are not required as permanent
project deliverables.

The FoundryEvals adapter is an explicit compatibility path. When the pinned
environment cannot invoke FoundryEvals, it records `NOT_RUN` and leaves the
deterministic LocalEvaluator as the ground-truth layer.
