# Phase 6 Three-Minute Demo Script

This script is bounded to the evidence currently available. Replace no metric
with an invented customer or production claim.

## 0:00–0:25 — Problem

> Autonomous agents can inspect systems and propose operational actions, but a
> useful-looking trajectory may be looping, wasting calls, or declaring success
> after an API merely accepted a request.

Show the incident goal:

```text
Restore the checkout service safely.
```

## 0:25–0:55 — Failure without the control plane

Show the bounded OFF comparison:

```text
dns_resolution → service_status → dns_resolution → service_status
4 executed calls, 2 repeated calls, no containment
```

Say:

> The agent is active, but activity is not objective progress.

## 0:55–1:35 — ReasonFuse detects the trajectory

Show the ON comparison:

```text
dns_resolution → service_status → dns_resolution → BLOCK
3 executed calls, 1 blocked proposal
fuse_reason = OSCILLATING
```

Say:

> ReasonFuse observes the normalized trajectory before dispatch. Once the
> bounded detector trips, the next operational call does not execute.

If using the local scenario matrix, show the parallel result:

```text
Todo changed, but objective evidence did not.
NO_PROGRESS → COMPLETE_AND_CONTAIN → BLOCK
```

## 1:35–2:15 — Accepted is not verified

Show the deterministic outcome path:

```text
restart_service → accepted / 202
service_status → UNHEALTHY
POSTCONDITION_FAILED
```

Say:

> An accepted side-effect response is not success. ReasonFuse reserves a
> verification read and classifies the fresh observation as verified, failed,
> or unknown.

Do not call this a live native approval demo unless the approval and cloud
Operations trace have been captured for the current submission.

## 2:15–2:40 — Capability view

Display:

```text
Trajectory Guard        ACTIVE
Progress Accounting     STALLED / PROGRESS
Failure Detection       OSCILLATING or NO_PROGRESS
Execution Contract      BOUNDED
Approval Control        NATIVE INTEGRATION (cloud proof pending)
Outcome Verification    VERIFIED / FAILED / UNKNOWN
```

## 2:40–3:00 — Technical moat and close

> Foundry runs the agent. ReasonFuse is the deterministic reliability layer
> between the agent and real-world actions. It measures objective progress,
> bounds unproductive execution, respects native approval, and verifies what
> actually happened.

Close with:

> ReasonFuse makes autonomous agent actions productive, bounded, and
> verifiable.

## Presenter guardrails

- The local fixture is a demo-safe in-memory Operations world, not production.
- The local 15-scenario matrix is not a benchmark or model-quality score.
- Native approval, cloud outcome verification, live Application Insights,
  Toolbox/IQ, APIM, and the final video are not claimed as complete without
  fresh evidence.
- Do not claim customer ROI or a percentage improvement beyond the measured
  local comparison table.
