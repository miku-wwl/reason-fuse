# Bounded Hosted Agent cloud E2E

This document records the bounded cloud behavior that was actually exercised
for the frozen ReasonFuse submission. It is a compact evidence index, not a
live endpoint and not production certification. The temporary Operations MCP
resources used for the run were deleted after evidence capture.

## Runtime

| Field | Observed value |
|---|---|
| Hosted Agent | `reasonfuse:6` |
| Responses protocol | `2.0.0` |
| Model | `gpt-5-mini` |
| Normal Hosted history contract | `history_source="agent_server"` |
| Normal Hosted storage contract | `store=False` |
| Operations boundary | bounded deterministic MCP fixture |

## Approval and fresh outcome

The observed sequence was:

```text
BEFORE: resource=orders, service_health=UNHEALTHY, generation=g1
→ native MCP approval request for operations___restart_service
→ no execution result before approval
→ approved restart
→ accepted=true, status_code=202, operation_id=demo-orders-g2
→ execution_count=1, side_effect_count=1
→ fresh operations___service_status observation
→ resource=orders, service_health=HEALTHY, generation=g2
→ OUTCOME_VERIFIED
```

The accepted response was not treated as success. The success decision came
from the fresh postcondition observation.

Selected identifiers from the captured Responses exchange:

| Evidence | Identifier |
|---|---|
| Initial approval response | `caresp_056ea5e7e674407f00rsT0dNLLr6TZ6PaWioY0X0ZTjC1P4Ak5` |
| MCP approval request | `mcpr_056ea5e7e674407f00z3H2C8lHmF9hVoxQd4ZmNJELh8Cuu5mZ` |
| Approved response | `caresp_056ea5e7e674407f00q9yi8kYCb7DMnnOl3HKfvWxt5AJxf6qT` |
| Fresh verification response | `caresp_056ea5e7e674407f003dWSzoqbPwROj6whaBM8d1IBQAU9xD5K` |
| Final runtime-state response | `caresp_056ea5e7e674407f00CSRHKoxtNTcSTc71Z1RnoaMAlWZKVnsJ` |

## Containment and no replay

Repeated equivalent status observations created a no-progress trajectory:

```text
repeated no-progress
→ `fuse_reason=NO_PROGRESS`, `contained=true`
→ subsequent restart proposal returned `decision=BLOCK`
→ no second side effect
→ `side_effect_count` remained `1`
```

Selected identifiers:

| Evidence | Identifier |
|---|---|
| Runtime after repeated stalls | `caresp_056ea5e7e674407f00PElx8tNqfZX9Pa1n3v8pliFjpeqCk51P` |
| Blocked proposal | `caresp_056ea5e7e674407f00auv9kWf9gkubhl41Pf0xeN655QWj4E4U` |
| Approved-after-fuse response | `caresp_056ea5e7e674407f00jLQR4p4lKLpb8yaU6vsJBcEdCVfuQDGV` |
| Final blocked runtime | `caresp_056ea5e7e674407f00e1HO8f5kQZ40dO3kzyWuDqO4h9BIkox4` |

No accidental replay: **PASS**.

## Continuation boundary

The approval continuation used `store=True` temporarily. A
`previous_response_id` continuation with `store=False` did not retain the
server-side response state required for this approval exchange. The normal
frozen Hosted request remains `store=False`; this document does not claim that
the approval continuation itself passed with `store=False`.

## Cloud observability boundary

Application Insights and cloud custom tracing were **NOT CONFIGURED** for this
bounded audit. No cloud `AppTraces`, custom ReasonFuse span, or
`REASONFUSE_FUSE_TRIPPED` telemetry event is claimed. The containment result
above is behavioral evidence from the Hosted exchange and runtime state.

Foundry IQ native retrieval was **NOT VALIDATED**. APIM/canary was removed from
the final scope. The temporary Operations MCP fixture is not a production
Operations backend.

## Cleanup

Temporary cloud Operations resources were removed after evidence capture to
avoid ongoing cost. The source remains in
[`cloud/operations-mcp/`](../../cloud/operations-mcp/README.md) and can be
redeployed for a new bounded validation run.
