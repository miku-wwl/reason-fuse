# Phase 2 Core Verification — Open Questions

## Independent gate status

There are no unresolved blockers for the documented Phase 2 P0 validation
scope. The independent batch passed and the final index is
[verification-20260909T110000Z/index.json](../../../evidence/phase-02-core/verification-20260909T110000Z/index.json).

The two retained failures were setup issues, not unresolved core failures:

- Missing `PYTHONPATH=src` caused the first local unit command to fail with
  `ModuleNotFoundError`; the corrected rerun passed 36 tests.
- The first fresh deployment hit a transient Azure CLI token acquisition
  timeout; the subsequent audited deployment and all downstream gates passed.

They remain in the main report and evidence index for auditability.

## Boundaries for a higher-level model

These questions were intentionally not converted into PASS claims:

1. **Foundry IQ retrieval.** Does native Foundry IQ preserve the same normalized
   source, citation, chunk/content-hash and knowledge-base-version semantics
   proven by the deterministic Toolbox fixture? Hosted retrieval churn is
   therefore `PASS` for the fixture only; Foundry IQ integration is
   `NOT VERIFIED`.
2. **Production Operations backend.** Do real restart and health endpoints
   expose a reliable fresh generation and health observation with the same
   accepted/failure/unknown semantics? The current evidence uses the
   deterministic Operations API fixture.
3. **Cloud Core trace correlation.** Can a collector query return the
   `reasonfuse.*` decision attributes/events for a new B/F/G/I run and correlate
   them to the request/session IDs? Local span emission and hosted runtime
   decision state passed as separate layers, but cloud collector correlation is
   `NOT VERIFIED`.
4. **Concurrency and forked turns.** Does state, budget reservation, pending
   postcondition binding and useful-recheck allowance remain safe under
   concurrent/forked turns, cold starts and more than one action in flight?
   These are outside the P0 one-action scope.
5. **Restart durability.** Does a process restart preserve the intended
   serialized AgentSession state and pending postcondition without resetting
   counters or creating a new run? The required multi-turn/native-approval
   behavior was exercised in the current deterministic path, but a separately
   isolated production restart durability campaign is still desirable.

## Suggested next work

The next model should create a separate, explicitly scoped campaign for the
questions above. It should preserve the current independent index and reports,
use new batch names, retain all setup/quota failures, and avoid weakening the
current P0 gates. No Phase 2 runtime change is required by this report.

## Final state

The final deployment was restored to enabled ON with contract `{}` on stable and
candidate, both agents active and sharing the audited package hash. The final
reset readback is [reset.jsonl](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T021517872355Z-reset.jsonl).
