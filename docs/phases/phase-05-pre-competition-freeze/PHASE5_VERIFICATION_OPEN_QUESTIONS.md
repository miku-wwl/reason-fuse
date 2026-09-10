# Phase 5 Pre-Competition Freeze — Open Questions

## Status

No unresolved local implementation blocker was found. The Phase 5 local RC1
verification result is PASS.

The items below are deliberately separated from the PASS result because they
require a later release decision, fresh authorization, or a live Azure
environment. They are not unfinished local implementation work.

## 1. Prompt path naming

The user-facing nested path
`ReasonFuse\\_Phase5\\_PreCompetition\\_Freeze\\_Verification\\_Prompt.md`
is not tracked in the current repository. The authoritative prompt is the
root-level file:

`ReasonFuse_Phase5_PreCompetition_Freeze_Verification_Prompt.md`

No duplicate prompt tree was created. If a future repository layout requires
the nested path, it should be handled as an explicit documentation move, not
as an additional verification artifact.

## 2. Final commit and release manifest snapshot

The verification report, this open-questions file and the
`REASONFUSE_EVIDENCE_ROOT` isolation fix are intentionally pending the next
commit. The generated manifest therefore records `working_tree_dirty=true` and
must be regenerated after the final repository change set is committed.

The proposed competition tag remains uncreated and requires a separate explicit
release decision.

## 3. Live Hosted revalidation

The last Phase 4 Hosted evidence is retained in the repository, but this turn
did not recreate Azure resources. A future live run would be required only if
the competition submission needs current platform evidence rather than the
retained Phase 4 handoff. That run would require separate authorization and
budget.

The current status is therefore:

```text
HOSTED NOT VERIFIED THIS TURN — intentional budget boundary
```

## 4. Official competition brief

The adaptation gap file is still a template because no official brief was
available to this verification. Once the brief exists, presentation or
submission packaging can be compared against it without changing the frozen
runtime baseline.

## 5. Resolved during this verification

The documented temporary evidence-root behavior was initially incorrect because
`scripts/phase2_local.py` ignored `REASONFUSE_EVIDENCE_ROOT`. This was fixed and
the corrected temporary-root run passed. It is recorded here for traceability,
not as an open blocker.
