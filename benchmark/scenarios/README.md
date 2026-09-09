# Scenario storage

The current canonical Phase 3 scenario source is the curated Agentathon profile
at `benchmark/datasets/reasonfuse_v2.jsonl`. It contains 15 scenarios: three per
detector category. The older v1 file is not the active construction input.
Category-specific scenario folders are intentionally not duplicated: keeping one
source prevents the runner and dataset schema from drifting apart.
