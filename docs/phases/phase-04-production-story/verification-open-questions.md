# Phase 4 Production Story — Verification Open Questions

## 1. Live Hosted re-run

- Status: `NOT VERIFIED THIS TURN`.
- Cause: `az group exists --name rg-reasonfuse-phase4c-aue` returned `false`; the temporary Azure environment was intentionally removed after the earlier bounded run.
- Impact: this turn cannot independently repeat live APIM routing, Native Foundry IQ, Operations, cloud trace, hosted SSE, rollback or cold-start without redeployment and additional budget.

## 2. Evidence form versus runtime result

- The prior Hosted PASS results are preserved in `PHASE4_CLOUD_VERIFICATION_REPORT.md` and `PHASE4_REPORT.md`.
- Raw JSONL Hosted evidence was intentionally removed after the earlier run, so this turn verifies the retained summary rather than re-reading raw cloud events.
- No retained summary is being upgraded to a new live PASS.

## 3. Judge Mode presentation client

- Runtime-state data was verified locally and through the prior Hosted `read_runtime_state` path.
- A separate browser/UI screenshot package was not produced. The updated Verification Prompt treats screenshots as optional presentation evidence, not a bounded P0 runtime requirement.

## 4. Test dependency

- The targeted `pytest` command could not start because `.venv` does not contain `pytest`.
- This did not block the executable Phase 4 demo scripts, preflight, compilation, JSON checks or their PASS assertions. Installing a test dependency was not performed because it was unnecessary for this budget-safe verification.
