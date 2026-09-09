# Scenario storage

The canonical Phase 3 scenario source is the versioned JSONL file at
`benchmark/datasets/reasonfuse_v1.jsonl`. Category-specific scenario folders
are intentionally not duplicated: keeping one source prevents the runner and
the dataset schema from drifting apart.
