# Phase 6 Submission Architecture

## One-sentence story

**Foundry runs the agent. ReasonFuse decides whether the run is still making
progress — and whether the real-world result was actually verified.**

## System boundary

```text
┌──────────────────────────────────────────────────────────┐
│ Microsoft platform                                      │
│ Foundry Hosted Agent · Responses 2.0.0                  │
│ Agent Framework · native approval                       │
│ Toolbox / Foundry IQ / Application Insights (optional)  │
└──────────────────────────────┬───────────────────────────┘
                               │ tool proposal/result
                               ▼
┌──────────────────────────────────────────────────────────┐
│ ReasonFuse deterministic control plane                   │
│                                                          │
│ Trajectory Guard → Progress Accounting → Failure Detect. │
│       → Execution Contract → Approval Control →          │
│         Outcome Verification → Observability             │
└──────────────────────────────┬───────────────────────────┘
                               │ allow / block / verify
                               ▼
┌──────────────────────────────────────────────────────────┐
│ Operations world                                         │
│ Terraform-declared App Service boundary                  │
│ `server.py` resettable demo fixture (local/demo safe)    │
└──────────────────────────────────────────────────────────┘
```

The six names are capabilities of one deterministic runtime. They are not six
LLM agents and do not change the frozen Phase 1–5 architecture.

## Capability ownership

| Capability | Owner | Current implementation |
|---|---|---|
| Trajectory Guard | ReasonFuse | pre-dispatch `ALLOW` / `BLOCK` |
| Progress Accounting | ReasonFuse | evidence, world, retrieval, todo and postcondition deltas |
| Failure Detection | ReasonFuse | exact loop, oscillation, retrieval churn and no-progress |
| Execution Contract | ReasonFuse | bounded steps, calls, stalls, side effects and verification reserve |
| Approval Control | Microsoft + ReasonFuse integration | native approval declaration plus side-effect accounting; cloud E2E not verified |
| Outcome Verification | ReasonFuse | fresh read → `OUTCOME_VERIFIED` / `POSTCONDITION_FAILED` / `OUTCOME_UNKNOWN` |
| Observability | Microsoft OTel/App Insights + ReasonFuse events | local structured events; live export not verified in this run |

## Demo flow

```text
Incident goal
    ↓
Hosted Agent proposes a diagnostic or side effect
    ↓
ReasonFuse calculates progress and contract state
    ├─ invalid trajectory → BLOCK before dispatch
    ├─ high-impact action → native approval required
    └─ accepted side effect → reserve and require a fresh read
    ↓
Operations fixture / real tool boundary
    ↓
Fresh observation
    ↓
verified, failed, or unknown outcome
```

## Claim discipline

The repository can currently show local deterministic evidence and retains a
bounded local-only Azure Hosted Agent claim from the v5.0.0 audit. It must not
describe `server.py` as a production Operations backend, or describe the
fixture's retrieval endpoint as native Foundry IQ. Native approval, cloud
postcondition verification, live telemetry export, Toolbox/IQ, and APIM remain
explicitly `NOT VERIFIED` until separately captured.

See [Phase 6 evidence](../../ReasonFuse_PHASE6_MICROSOFT_SUBMISSION_EVIDENCE.md)
and the [15-scenario contract](../../benchmark/15-scenarios.md).
