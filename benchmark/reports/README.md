# Phase 3 report pipeline

`generate_report.py` renders the batch-specific `PHASE3_REPORT.md` inside a
Phase 3 evidence directory. `index_artifacts.py` records SHA-256 hashes for
that batch. Raw and normalized JSONL are intentionally kept under
`evidence/phase-03-evidence-benchmark/verification-<UTC>/` so each run is
immutable and cannot silently overwrite a prior benchmark batch.

The FoundryEvals adapter is an explicit compatibility path. When the pinned
environment cannot invoke FoundryEvals, it records `NOT_RUN` and leaves the
deterministic LocalEvaluator as the ground-truth layer.
