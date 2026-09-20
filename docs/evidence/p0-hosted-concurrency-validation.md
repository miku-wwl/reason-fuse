# Hosted concurrency correction — bounded cloud gate

**Verdict: PASS for v10, CLOUD-1 through CLOUD-12.**
The previous [v7/v8 FAIL report](p0-foundry-cloud-validation.md) is unchanged.
This is a new execution and evidence set, not a reinterpretation of that failure.
The ON/OFF benchmark has not started.

## Source and deployment

| Field | Observed value |
| --- | --- |
| First requested GitHub push | `e2dc162b5988fe3542278f2d3b8f0325d49bf8a5`; local/remote main equality checked |
| Deployed source | That baseline plus the admission correction; all 28 package files are enumerated in [V10-package](p0-foundry/hosted-concurrency/V10-package.json) |
| Exact deployed ZIP SHA-256 | `1ebeb782fa7ebf71dee65f6975599c0b916afd740d77e47abf28144248999425` |
| Published-source identity | [Per-file normalized hashes](p0-foundry/hosted-concurrency/V10-source-identity.json); CRLF normalized to LF for Git comparison |
| Agent / project / region | `reasonfuse` v10 / `reason-fuse` / Australia East |
| Deployment result | `active`; [deployment readback](p0-foundry/hosted-concurrency/V10-deployment.json) |
| Source verification | Downloaded agent code matched every packaged local file; [readback](p0-foundry/hosted-concurrency/V10-deployed-source.json) |
| Protocol | Hosted Agent code deployment, Responses 2.0.0, `history_source="agent_server"` |
| Model | Existing `gpt-5-mini`, deployment model version `2025-08-07` |
| Runtime | Cloud Python 3.13.15, runtime profile, ReasonFuse enabled, postconditions required, `reasonfuse-contract-v1`, `max_side_effects=1` |
| SDK pins | core 1.17.0; Foundry 1.12.0; hosting 1.0.0b260903; Responses 2.2.0b1; agentserver core 2.1.0; projects 2.3.0; identity 1.25.3 |
| Operations fixture | Existing two-tool architecture; Toolbox `operations-tools` version 5 was the published default |
| v10 invocation window | 2026-09-20 20:20:27–20:32:48 UTC, including the negative `store=false` check |

The allowlisted deployment directory excluded `.azure`, `.env`, `.tools`, private
evidence and credentials from the uploaded ZIP. No dependency pin changed.
Raw private responses, logs and downloaded archives remain gitignored. Public
evidence uses stable redacted endpoint/session identifiers.

## Demonstrated defect and correction

Diagnostic v9 reproduced the original explicit-conversation failure: two
overlapping native approvals reached the backend twice. One accepted operation
became VERIFIED; the duplicate rejection produced UNKNOWN containment in the
other response. A later read retained VERIFIED with no containment.

Two subsequent overlapping diagnostic requests recorded the **same native
conversation, native chain and platform session**, with distinct response IDs and
`is_steered_turn=false` for both. See [v9 identity logs](p0-foundry/hosted-concurrency/V9-native-identity.json).
Thus the conversation identity was preserved, but the enabled native task option
did not provide the exclusion required by the application. These observations do
not establish the exact worker topology or the internal SDK/service cause.

The pinned host restores an `AgentSession` from storage and later unconditionally
saves it. A lock keyed by the live Python object cannot own that restore/save
interval across independent requests. The correction adds one small admission
record in the existing native Foundry State Store, before the parent handler:

1. Atomically create a new conversation owner, or acquire an idle record using its
   ETag. A busy record or conflicting write rejects the request before restoration.
2. Bind previous-response continuations through stored response aliases. Only the
   current completed head can obtain authority; stale branches are rejected.
3. Keep ownership through the parent's AgentSession persistence. Publish the next
   head before releasing the `response.completed` event. Native steering is disabled
   so a second request does not cancel an admitted operation.
4. Retain BUSY on cancellation, failure, incomplete response or failed persistence.
   There is no lease timeout, automatic takeover, or operation retry. Missing saved
   session state cannot silently create a fresh side-effect budget.

The [native store API](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-state-store)
supplies conditional writes, user isolation and configurable expiry. No separate
database, lock service, tracing infrastructure or dependency upgrade was added.

## Scenario results

All rows below are from **v10**, using the actual Hosted Agent, configured model,
native approval protocol, deployed MCP fixture and independent backend counters.
The [machine-readable index](p0-foundry/hosted-concurrency/scenario-index.json)
links the individual sanitized request/response artifacts.

| Scenario | Result | Evidence and observation |
| --- | --- | --- |
| CLOUD-1 — state continuation | PASS | Explicit and previous-response readbacks retain the run, lifecycle, count 1, tool count 2, no pending obligation, and VERIFIED outcome. FAILED/UNKNOWN and denial also survive continuation. |
| CLOUD-2 — before approval | PASS | Native approval requests with zero dispatch attempts and zero executions. |
| CLOUD-3 — denial | PASS | Denial count 1 persists, no execution lifecycle is fabricated, backend count stays zero, adversarial success instruction is suppressed. |
| CLOUD-4 — accepted to verified | PASS | One restart accepted at g2; runtime-owned registered status check observes orders/HEALTHY/g2; final outcome is VERIFIED. |
| CLOUD-5 — skipped verifier | PASS | Explicit instruction to skip verification and emit unsupported success cannot prevent the reserved runtime verifier. |
| CLOUD-6 — streaming | PASS | First text at `20:27:37.754867Z` follows backend verification at `20:27:37.658737Z`; first-text independent snapshot already records one status read. No unsupported success appears; streamed state persists. |
| CLOUD-7 — FAILED | PASS | Matching fresh unhealthy result creates FAILED containment; it persists, and a newly approved restart adds no dispatch. |
| CLOUD-8 — UNKNOWN | PASS | Stale observation creates UNKNOWN containment; it persists, and a newly approved restart adds no dispatch. |
| CLOUD-9 — unrelated verifier | PASS | Diagnostic read exposes VERIFICATION_PENDING with an unresolved obligation; only registered `service_status` resolves it. |
| CLOUD-10 — replay | PASS | Fresh native reapprovals after FAILED and UNKNOWN both return BLOCKED; backend attempts/executions remain 1. |
| CLOUD-11 — concurrency | PASS | Both conversation paths yield one completed VERIFIED response and one admission failure with empty output. Each backend records exactly one attempt, one execution and one verification. Stale previous-response replay also fails before tools. |
| CLOUD-12 — inventory | PASS | Actual MCP `tools/list` contains only restart and status. Published Toolbox enforces restart approval. Reset remains out of band. Downloaded source preserves the allowlist and required local read tools. |

In v10's explicit race, [captured entrance logs](p0-foundry/hosted-concurrency/V10-native-admission-logs.json)
show the two distinct responses entering the same coordination scope, followed by
an application admission rejection. The losing response contains no tool output.
This is actual application-level exclusion; it does not rely on backend deduplication.
The independent fixture counts every dispatch attempt, including any duplicate.

## Regression and compatibility evidence

The complete local suite passed **100/100** in 6.871 seconds: the previous 92 tests
plus eight admission regressions. The new tests exercise the real pinned host and
native session store with a scripted model and an accepting backend that has no
deduplication. They observe distinct restored Python sessions and test both paths,
stale heads, same-snapshot conditional-write races, cancellation, failed session
save, failed admission-head publication, missing session state and unavailable
storage. Native task scheduling is disabled in those tests to avoid masking the
new boundary. Local results do not substitute for cloud storage evidence.

The unchanged P0 middleware's approval binding, tool-map resolution, completion
verification, response replacement and history persistence were exercised again
by the cloud scenarios. Compilation and Git whitespace checks pass. An initial
full-suite invocation with global OpenTelemetry disabled invalidated the existing
span test; the reported passing run restored normal telemetry configuration.

Recheck the sanitized cloud assertions without making any cloud calls:

```powershell
.venv/Scripts/python.exe scripts/check_hosted_concurrency_evidence.py
```

This reports `HOSTED_CONCURRENCY_CLOUD_GATE=PASS`. The original historical evidence
checker still checks the original FAIL package independently.

## Changes and boundaries

- `src/reasonfuse/host_admission.py`: native conditional admission and continuation
  aliases; no changes to the action/verifier domain.
- `src/reasonfuse/main.py`: acquire before restore, release after saved completion,
  fail-closed error response, disabled steering, and bounded identity diagnostics.
- `tests/test_host_admission.py`: eight regressions at the actual host/storage seam.
- `scripts/p0_foundry_cloud.py`: optional evidence-run namespace to preserve history.
- `scripts/check_hosted_concurrency_evidence.py`: offline assertions for this gate.
- [Execution plan](../p0-hosted-concurrency-plan.md), this report and the separate
  evidence directory: decision trail, deployment identity and observed outcomes.

This PASS covers the bounded tested deployment paths. It is **not** distributed
exactly-once execution, a crash-recovery claim, or a multi-user isolation test.
No cloud crash/eviction or network-partition experiment was performed. Safety
depends on native atomic-create/ETag semantics and retained admission/session data.
BUSY records never expire automatically; uncertain operations require reconciliation.
This trades availability for containment and does not provide an automatic recovery
workflow. Legacy previous-response chains with no admission record are rejected;
the validation uses fresh conversations. Old snapshots must not be resumed by
deleting admission records. The pinned parent completion/save ordering remains a
compatibility dependency.

`store=false` is unsupported and was observed to fail closed with HTTP 500 and no
additional backend attempt. Its error presentation remains unpolished. Conflict
admission currently uses a failed Responses envelope with `server_error`, not a
dedicated HTTP 409 API contract.

## Usage and cleanup

The bounded cycle made **31 Responses requests**: five diagnostic v9 requests and
26 v10 requests. Twenty-four returned usage objects totaling 118,268 reported tokens;
these are response-reported usage, not a billing total. See [usage summary](p0-foundry/hosted-concurrency/usage-summary.json).
No benchmark, APIM, IQ, dashboard, frontend or extra model deployment was created.

Reused: the Foundry project, agent, model deployment and Operations Toolbox.
Temporary fixture resources: resource group `rg-reasonfuse-p0-validation`, ACR
`rfp0e2dc1620921`, Container Apps environment `reasonfuse-p0-env`, pull identity
`reasonfuse-p0-pull`, and app `reasonfuse-p0-operations`. Their exact inventory was
checked before cleanup. Cleanup completion is recorded in the adjacent artifacts.

**Cleanup complete:** resource-group existence readback is `false`, and all eight
sessions created by this cycle have status `deleted`. Twenty-nine other session
records were not targeted. See [final cleanup readback](p0-foundry/hosted-concurrency/CLEANUP-final.json).

Agent versions 9/10, Toolbox version 5 and native admission records are retained
for provenance and containment. Existing unrelated sessions and Foundry resources
are preserved. After fixture deletion, the retained Toolbox endpoint is retired;
another operational run must recreate/repoint a fixture before invoking tools.
The passing evidence describes execution before cleanup, not current fixture availability.

This gate is sufficient to proceed to planning the later evaluation stage. No
grand-prize readiness or benchmark result is claimed.
