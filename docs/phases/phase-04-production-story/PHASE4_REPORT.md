# Phase 4 Production Story Report

## Environment

- Construction: local deterministic runner, 15 scenarios, existing local repeatability retained.
- Hosted verification: fresh Australia East environment `rf-phase4c-20260910`; all temporary Azure resources were removed after the run.
- Model deployment used for hosted probes: `gpt-5-mini`.
- Detailed hosted results: [`PHASE4_CLOUD_VERIFICATION_REPORT.md`](PHASE4_CLOUD_VERIFICATION_REPORT.md).

## Stable / Candidate Matrix

| Field | Stable | Candidate |
| --- | --- | --- |
| Hosted agent version | 2 | 2 |
| Release role | stable | candidate |
| Model | gpt-5-mini | gpt-5-mini |
| Toolbox | `reasonfuse-operations` v2 | `reasonfuse-operations` v2 |
| Native IQ source | same Search index/KB | same Search index/KB |
| Run contract | `reasonfuse-contract-v1` | `reasonfuse-contract-v1` |

Both releases used the same model, Toolbox, Native IQ source, and ReasonFuse middleware. The controlled Candidate-only difference was the explicitly seeded DNS repetition instruction.

## APIM / Trace / Judge Mode

- Weighted canary: **PASS**, Stable 95 / Candidate 5.
- Persistent affinity: **PASS**, same client remained on Stable across turns; fresh client received an independent assignment.
- SSE: **PASS**, 52 incremental chunks through APIM.
- Real Operations: **PASS**, authoritative middleware `BEFORE`/`AFTER` events and runtime state were returned.
- Judge Mode data path: **PASS**, runtime-state evidence exposed release role, tool sequence, trajectory state, ReasonFuse decision and containment state.
- Cloud trace: **PASS**, the bounded run correlated APIM `AppRequests` with ReasonFuse `AppTraces` and `reasonfuse_*` properties.

## Native Foundry IQ

**PASS.** Stable and Candidate both made a real Hosted Agent function call named `foundry_iq___knowledge_base_retrieve` through the versioned Toolbox. The returned source key was `rf-phase4-iq-001`; the grounded answer stated that a repeated no-progress loop is blocked and `service_status` is the useful recheck. This path used the Foundry project `RemoteTool` connection and Azure AI Search Knowledge Base MCP, not `retrieval_fixture`.

## Signature Demos

| Demo | Local repeatability | Clean-start replay | Result |
| --- | ---: | ---: | --- |
| OFF / ON | 3 | 1 | PASS |
| Unknown Correct Path | 3 | 1 | PASS |
| Outcome Failure | 3 | 1 | PASS |
| Candidate Regression | 3 | 1 + hosted Stable/Candidate | PASS |

Hosted Candidate regression proof:

```text
Stable:    dns_resolution(INCONCLUSIVE) → service_status → PROGRESS
Candidate: dns_resolution(INCONCLUSIVE) → dns_resolution → NO_PROGRESS/STALLED/contained
```

## Rollback and Cold-Start

- Rollback: **PASS**, APIM changed to Stable 100 / Candidate 0; new sessions routed Stable.
- Hosted cold-start: **PASS**, the official managed-session stop/resume lifecycle restored marker, state and turn continuity.

## Clean-Start E2E

**PASS.** From the fresh environment, the run completed:

```text
preflight → Judge Mode runtime_state → OFF/ON
→ Unknown Correct Path → Outcome Failure
→ Candidate Regression → rollback → Stable recovery
```

The first post-deployment APIM request had a transient warm-up 504; after the deployments became active, the final clean-start sequence passed. The warm-up observation is recorded in the cloud report.

## Phase 4 Result

```text
PHASE 4 RESULT: BOUNDED P0 PASS
```

The two previously open items—Hosted Stable/Candidate Native IQ MCP invocation and full clean-start E2E—are resolved. Remaining work is optional presentation packaging or larger-scale evaluation, not a Phase 4 P0 blocker.
