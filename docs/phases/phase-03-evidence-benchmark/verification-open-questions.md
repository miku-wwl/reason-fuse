# Phase 3 — Open Questions and Boundaries

## Resolved for the Agentathon profile

- The active dataset contains 15 scenarios, three per detector category.
- The default runner executes one repetition per scenario.
- Local deterministic execution completed 15/15 valid runs.
- OFF/ON comparison completed 15 controlled pairs.
- The local confusion matrix was independently recomputed as TP 12, FP 0,
  TN 3, FN 0.
- No Azure or model calls are required for the bounded profile.

## Scope boundary

The retained verification is intentionally local and deterministic. The profile
does not require provider calls, a cloud deployment, extra execution modes or
extra scoring layers.

## Decision boundary

The 15-scenario profile is the complete Microsoft Agentathon demonstration
profile. It must not be presented as a statistical production regression suite.

## Reproduction

Run the local suite against `benchmark/datasets/reasonfuse_v2.jsonl` with
`--repetitions 1`. Store any raw files in a temporary directory and remove them
after the report has recorded the result.
