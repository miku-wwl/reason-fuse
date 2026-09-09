# Scenario storage

The current canonical Phase 3 scenario source is the repaired v2 JSONL file at
`benchmark/datasets/reasonfuse_v2.jsonl`. The v1 file is retained as historical
construction evidence and is not the active construction input. Category-specific
scenario folders are intentionally not duplicated: keeping one source prevents
the runner and the dataset schema from drifting apart.
