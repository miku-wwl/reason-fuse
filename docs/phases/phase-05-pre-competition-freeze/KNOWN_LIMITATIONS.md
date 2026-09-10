# ReasonFuse Competition RC1 — Known Limitations

- The default Phase 5 commands are budget-safe and do not deploy Azure.
- The last Hosted Phase 4 environment was intentionally deleted; live APIM,
  Foundry IQ, Operations, cloud trace and platform cold-start checks require a
  separately authorized redeployment.
- Phase 4 Hosted results are retained as summarized evidence; raw cloud JSONL
  was intentionally removed after the bounded run.
- The active benchmark is the local `15 scenarios × 1 run` deterministic gate.
- The frozen rollback requirement is that new sessions route Stable.
- Application Insights/Log Analytics ingestion can lag during a Hosted run and
  must be validated with a bounded wait.
- Browser screenshots are optional presentation evidence, not runtime proof.
