# Phase 3 — Open Questions and Boundaries

## Resolved for the Agentathon profile

- The active dataset contains 15 scenarios, three per detector category.
- The default runner executes one repetition per scenario.
- Local deterministic execution completed 15/15 valid runs.
- OFF/ON comparison completed 15 controlled pairs.
- The local confusion matrix was independently recomputed as TP 12, FP 0,
  TN 3, FN 0.
- No Azure or model calls are required for the bounded profile.

## Still not verified

| Area | Status | Reason |
| --- | --- | --- |
| Foundry IQ native retrieval | NOT VERIFIED | No live Search connection was provisioned |
| Production Operations backend | NOT VERIFIED | Local deterministic fixture only |
| Cloud Core trace correlation | NOT VERIFIED | No active cloud deployment |
| Concurrent/forked turns | NOT VERIFIED | Outside the local fixture profile |
| Cold-start recovery | NOT VERIFIED | No production platform restart was performed |
| ToolCallAccuracy model quality | NOT RUN | Deliberately avoided billable model calls |

## Decision boundary

The 15-scenario profile is sufficient for the Microsoft Agentathon demonstration
and competition narrative. It must not be presented as a statistical production
regression suite. A larger model-backed evaluation should only be run later with
an authorized account, an explicit budget, and a separately recorded purpose.

## Reproduction

Run the local suite against `benchmark/datasets/reasonfuse_v2.jsonl` with
`--repetitions 1`. Store any raw files in a temporary directory and remove them
after the report has recorded the result.
