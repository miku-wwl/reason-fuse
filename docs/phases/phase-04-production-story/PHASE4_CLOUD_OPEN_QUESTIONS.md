# Phase 4 Cloud Validation — Open Questions

## Resolved P0 items

- Native Foundry IQ MCP invocation: **RESOLVED/PASS** for Stable and Candidate. Both deployed releases called `foundry_iq___knowledge_base_retrieve` through the shared versioned Toolbox and returned the pinned source/citation.
- Full clean-start E2E: **RESOLVED/PASS** in a fresh Terraform/azd environment. APIM 95/5, affinity, SSE, Operations, Judge Mode runtime state, Candidate regression, rollback and Stable recovery were exercised.
- Hosted-session cold-start: **RESOLVED/PASS** in the bounded official stop/resume lifecycle.
- Cloud trace correlation: **RESOLVED/PASS** in the bounded Log Analytics query.

## Non-blocking follow-up

- A competition presentation may capture fresh UI screenshots of Judge Mode and the release/affinity evidence. This is presentation packaging, not a Phase 4 runtime blocker.
- Large-scale repeated hosted evaluation remains intentionally out of scope because the project was reduced to 15 scenarios × 1 run for budget control.
