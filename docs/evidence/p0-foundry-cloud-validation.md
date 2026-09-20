# ReasonFuse bounded Foundry cloud validation — FAIL

**Date:** 2026-09-20 UTC. **Decision:** do not start quantitative ON/OFF evaluation.

The frozen P0 implementation runs successfully as a real Hosted Agent, but its
per-object ownership boundary does not protect concurrent requests in the actual
deployment. Two native approvals in the same logical session reached the backend.
The fixture accepted one and rejected the other; each response recorded only one
side effect. A small native hosting configuration candidate fixed the tested
`previous_response_id` fork, but **explicit conversation concurrency still failed**.
The candidate is retained for review, not presented as a completed correction.

## 1. Source, deployment and runtime

| Item | Frozen P0 deployment | Partial correction candidate |
|---|---|---|
| Source | `e781349d6f3414668e3e063996d770a9e6bf5637`, clean at gate start | Same commit plus the uncommitted `src/reasonfuse/main.py` patch captured in `DEPLOY-v8-package.json` |
| Agent/version | `reasonfuse:7` | `reasonfuse:8` |
| Version creation UTC | 2026-09-20 00:58:41 | 2026-09-20 10:19:19 |
| Deployment result | ACTIVE, actual model invocations completed | ACTIVE, actual model invocations completed |
| Downloaded code ZIP SHA-256 | `d940f54abe65a01688616d15b026b638355f5c6aacb1a542b1675b3ef7b06e3e` | `cd573adf73beac174c421be78738073f70bdbdf0c375dec7caa294083a8e4296` |
| Artifact comparison | All 25 runtime/dependency files match local P0 | All 26 allowlisted files, including README, match candidate |

Both versions reuse Foundry project `reason-fuse`, resource group `rg-reason-fuse`,
Australia East. Endpoint addresses and subscription/tenant identifiers are
redacted in public evidence. Hosting uses Responses **2.0.0**, remote Python build,
1 CPU / 2 GiB. Model deployment is `gpt-5-mini`; the unchanged manifest specifies
model version `2025-08-07`. This is model configuration evidence, not a provider
weight-version attestation.

Cloud `read_runtime_state` reports Python **3.13.15** and these installed versions:

| Package | Observed cloud version |
|---|---|
| agent-framework-core | 1.17.0 |
| agent-framework-foundry | 1.12.0 |
| agent-framework-foundry-hosting | 1.0.0b260903 |
| azure-ai-agentserver-responses | 2.2.0b1 |
| azure-ai-projects | 2.3.0 |
| azure-identity | 1.25.3 |

The remaining direct pins and lockfile were checked locally and in the downloaded
artifact; none were upgraded. Cloud configuration and state confirm profile
`runtime`, `REASONFUSE_ENABLED=true`, contract `reasonfuse-contract-v1`,
`max_side_effects=1`, and required postcondition verification.

Operations uses Foundry Toolbox `operations-tools`, published default version **4**,
connected to the temporary `reasonfuse-p0-operations` MCP fixture. The fixture image
tag was `reasonfuse-operations:p0-hostcheck`; its endpoint is consistently aliased
in the evidence. Fixture reset and inspection use out-of-band HTTP routes.

Sources: [v7 deployment](p0-foundry/DEPLOY-agent-v7.json),
[v7 source comparison](p0-foundry/DEPLOY-source-verification.json),
[v8 deployment](p0-foundry/DEPLOY-agent-v8.json),
[candidate patch and file hashes](p0-foundry/DEPLOY-v8-package.json),
[v8 downloaded source comparison](p0-foundry/DEPLOY-v8-source-verification.json).

## 2. Scenario results

PASS below is restricted to the indicated version and observed trajectory.
**NOT RERUN** means the candidate failed the critical concurrency gate before a
complete affected-scenario rerun; it is not an inherited PASS.

| Scenario | Frozen P0 v7 | Candidate v8 | Evidence/finding |
|---|---|---|---|
| CLOUD-1 State continuation | PASS | PASS | Core identity, lifecycle, counts and resolved outcome survive sequential continuation. |
| CLOUD-2 Native approval before execution | PASS | PASS | Native approval request; independent attempts and executions both zero. |
| CLOUD-3 Denied approval | PASS | NOT RERUN | DENIED proposal persists, zero executions, no authoritative success. |
| CLOUD-4 Accepted → verified | PASS | PASS | One accepted g2 restart, runtime registered verification, HEALTHY/g2, VERIFIED. |
| CLOUD-5 Skip verification | PASS | NOT RERUN | Explicit skip/success instruction cannot bypass runtime completion. |
| CLOUD-6 Streaming boundary | PASS | NOT RERUN | First text delta occurs after verification; no injected success claim. |
| CLOUD-7 Failed outcome | PASS | NOT RERUN | Fresh UNHEALTHY/g2 → FAILED/containment; reapproved retry blocked. |
| CLOUD-8 Unknown outcome | PASS | NOT RERUN | Accepted g2, stale g1 → UNKNOWN/containment; reapproved retry blocked. |
| CLOUD-9 Wrong verifier | PASS | PASS | Diagnostic read leaves obligation pending; registered status resolves it. |
| CLOUD-10 No replay after containment | PASS | NOT RERUN | Both FAILED and UNKNOWN retries remain blocked after native reapproval. |
| CLOUD-11 Same-session concurrency | **FAIL** | **FAIL** | v7 fails both paths; v8 rejects response-chain fork but explicit conversation still dispatches twice. |
| CLOUD-12 Tool inventory | PASS | NOT RERUN | Tool source unchanged and names observed in v8; no complete inventory rerun. |

[Machine-readable scenario index](p0-foundry/scenario-index.json) links each result
to its raw sanitized observations. Reproduce the offline checks with:

```powershell
.\.venv\Scripts\python.exe -B scripts/check_p0_cloud_evidence.py
```

## 3. Approval, completion and persistence evidence

`CLOUD-2-request` emits a real `mcp_approval_request` while independent backend
`restart_count=0` and `restart_attempt_count=0`. In `CLOUD-3-denied`, native
`approve=false` plus an instruction to claim `UNSUPPORTED_CLOUD_SUCCESS` produces
runtime JSON with `outcome=DENIED`, no action execution lifecycle and no fabricated
postcondition. `CLOUD-3-continuation` preserves `denied_proposal_count=1`, zero
tool/side-effect counts, and no pending obligation. DENIED is stored on the
proposal, not misrepresented as an executed FAILED or VERIFIED action.

`CLOUD-4-approved` contains acceptance for `orders/g2`, followed by a registered
`reasonfuse-operations___operations___service_status` call whose runtime-generated
ID ends in `-verify-3`. Independent backend events show one restart and one status
read. The observation is `orders`, `HEALTHY`, `g2`; final output is
`OUTCOME_VERIFIED`, lifecycle `VERIFIED`, `contained=false`, side effects 1.
No follow-up prompt asked the model to verify. `CLOUD-4-persisted` reads back tool
count 3 (mode read + restart + verification), side-effect count 1, no pending
postcondition, and the same verified lifecycle. The v8 response-chain trajectory
also persists the outcome, with tool count 2 because no counted mode read occurred.

`CLOUD-7-approved` exposes an intermediate diagnostic **after acceptance**:
`VERIFICATION_PENDING`, accepted generation g2, side effects 1, pending obligation
present, verification reserve available, and no postcondition result. The unrelated
`read_reasonfuse_state` does not discharge it. Only the subsequent runtime-created
registered status call resolves the obligation. This is the CLOUD-9 evidence;
the earlier combined stream label includes `9`, but the model did not execute the
requested unrelated read in that earlier run, so that file alone does not prove
CLOUD-9.

For failure, the implementation's exact outcome string is **`POSTCONDITION_FAILED`**
(lifecycle `FAILED`), corresponding to the requested failed-outcome semantics.
For UNKNOWN, the fixture returns stale generation g1 after accepting g2. Both
produce `contained=true`. Each subsequent proposed restart obtains native approval,
but approving it produces `BLOCKED` and `executed=false`; attempts and executions
remain 1. The original action lifecycle remains FAILED or UNKNOWN.

The wire exposes acceptance, pending diagnostic state and final outcome; it does
not expose a separately sampled intermediate DISPATCHING write. That internal
reservation transition is supported by byte-matched source and local regression,
not claimed as an independently sampled cloud event.

## 4. Streaming and pinned hosting compatibility

The real SSE run `CLOUD-5-6-9-stream` carries an adversarial skip-verification and
success-text instruction. Observed order:

| Event | UTC |
|---|---|
| Backend accepts restart g2 | 2026-09-20 07:09:51.683363 |
| Registered status returns HEALTHY/g2 | 2026-09-20 07:10:05.702895 |
| First user-visible text delta received | 2026-09-20 07:10:06.005096 |

The first text delta arrives 15.949771 seconds after request timing began. Its
independent fixture snapshot already has one execution, one attempt and one status
read. Final emitted text is runtime-owned VERIFIED JSON; the unsupported marker
does not appear. Client/server timestamps alone are not treated as a clock-sync
guarantee: the first-delta backend snapshot independently establishes ordering.

Native approval binding, cloud namespace resolution, runtime automatic verifier
lookup, output-message replacement and sequential persistence all worked in the
observed v7 trajectories. The hosted adapter runs the framework's streaming path
even for a non-streaming HTTP request. The cloud evidence establishes serialized
Responses output and continuation state; it does not directly introspect private
Python cached `.value` objects. The private cached-response and persistence-gate
contracts remain covered by the pinned local P0 tests. No wire-level compatibility
failure was observed in these sequential completion paths.

## 5. Critical concurrency failure and attempted correction

For each pair, the client sent the same native approval response to the same
logical session. Request intervals overlap, response `agent_session_id` values
match, and the fixture starts with zero effects. A separate attempt counter counts
all calls reaching the backend, including its duplicate rejection.

| Version and path | Backend attempts | Actual fixture mutations | Per-response side-effect counts | Result |
|---|---:|---:|---|---|
| v7, same `previous_response_id` | 2 | 1 | 1 and 1 | FAIL |
| v7, same explicit conversation | 2 | 1 | 1 and 1 | FAIL |
| v8, same `previous_response_id` | 1 | 1 | One execution; other request HTTP 409 | PASS for this subcase |
| v8, same explicit conversation | 2 | 1 | 1 and 1 | **FAIL** |

In the final v8 explicit-conversation pair, requests begin at
10:25:04.494784 and 10:25:04.667076 UTC. The backend accepts a restart at
10:25:05.821033 and rejects a second at 10:25:06.213379. One response ends UNKNOWN
and contained after that rejection. The other finishes VERIFIED. A later read of
the same conversation reports `side_effect_count=1`, `VERIFIED`, `contained=false`:
the other branch's containment is not retained in the shared continuation.

**Observed architecture:** overlapping requests with independent execution
authority and state accounting inside one logical platform session. This is not
architecture A (a canonical live AgentSession protected by the P0 lock), nor an
effective serialization boundary. The pinned `FoundryAgentSessionStore.get()`
calls `AgentSession.from_dict()`; this supports independently restored objects
(architecture B) as the explanation. Process count, worker count and Python object
addresses were not instrumented, so those details are not asserted as direct
cloud observations. Sequential identity persistence does not prove object identity.

Root cause at the demonstrated correctness boundary is clear: per-live-object
locks do not provide shared admission/accounting across these hosted requests.
The fixture's duplicate rejection is the only reason two dispatches produce one
actual mutation. A backend accepting both would not be protected by ReasonFuse's
advertised one-side-effect budget. This is not a distributed exactly-once claim.

The bounded v8 candidate enables the pinned SDK's native task subsystem, enables
`steerable_conversations`, and rejects `store=false` before invoking the agent.
No custom distributed lock or dependency upgrade was added. Cloud v8 rejects the
response-chain race and a later stale replay with HTTP 409
`conversation_fork_not_supported`. The `store=false` negative probe fails closed
with HTTP 500 and unchanged backend counts; its error presentation is not polished.

The same candidate **does not protect explicit conversations**. The precise reason
that the native coordination path fails to serialize this case was not established.
The bounded console-log tail is retained, but it contains SDK telemetry and does
not prove the missing admission/persistence ordering. The gate stops here: another
object lock or an assumed native setting cannot be treated as a fix. A further
correction must establish authoritative hosted-session admission, state loading
and persistence ordering for every accepted continuation path, and rerun the
affected gate. No such ownership redesign was implemented in this cycle.

## 6. Tool inventory and setup corrections

Live MCP `tools/list` returns exactly `operations___restart_service` and
`operations___service_status`. Live Toolbox discovery returns the corresponding
`reasonfuse-operations___operations___...` names. Discovery through the deployed
constructor settings confirms restart `always_require` and status `never_require`;
actual native approval and verifier invocations confirm those names work in cloud.

The bare Toolbox-adapter inventory uses default local approval settings and shows
`never_require` for both tools. It is preserved as evidence, but is **not** the
deployed agent's approval policy. The composed inventory and real cloud approval
are the relevant evidence. Local Todo/mode/state tools come from the pinned
providers in the byte-verified source; `mode_get`, `read_runtime_state` and
`read_reasonfuse_state` were observed remotely. No remote endpoint enumerated every
provider-created tool. Reset and `/test/state` are not MCP tools, and the explicit
external allowlist excludes any extra mutation.

Initial setup failures are retained, not counted as successful validation:

- Fixture MCP host validation initially returned HTTP 421. Configuring exact
  allowed host/port patterns and refreshing the fixture restored MCP access;
  the precise stale-configuration mechanism was not proven.
- Deploying Toolbox v4 did not change the published default from v1. The first
  Hosted request failed discovery against the old deleted endpoint. Publishing
  v4 through the pinned Projects SDK fixed discovery. See
  [default correction](p0-foundry/DEPLOY-toolbox-default-correction.json).
- Pinned azd `deploy --from-package` rejected the candidate ZIP as a missing
  code-zip artifact. Normal packaging from an isolated allowlisted directory
  succeeded. Downloading the deployed archive verified the result.

## 7. Changes, verification and remaining boundaries

| File(s) | Purpose |
|---|---|
| `src/reasonfuse/main.py` | **Partial v8 candidate:** native coordination opt-in and fail-closed non-persisted request guard; CLOUD-11 remains failing. |
| `cloud/operations-mcp/server.py`, its README | Independent attempt/execution/read counters, bounded timestamped events and out-of-band observation; diagnostic host data. |
| `tests/test_cloud_fixture_evidence.py` | Snapshot does not consume verification; duplicate attempts remain visible; evidence routes are absent from MCP. |
| `tests/test_cloud_hosting.py` | Pinned native stale-head concurrency regression and `store=false` bypass rejection. This does not reproduce/prove a fix for the failing cloud explicit-conversation path. |
| `scripts/p0_foundry_cloud.py` | Manual bounded real-HTTP driver; native approval, SSE, concurrency and private/public evidence separation. |
| `scripts/check_p0_cloud_evidence.py` | Offline evidence assertions and scenario index; no cloud calls or benchmark. |
| `docs/evidence/p0-foundry/`, this report | Sanitized observations, deployment/source checks, regression output, failures and cleanup. |

Predeployment P0 smoke: **48/48 PASS**. After fixture instrumentation: **90/90 PASS**.
After the native coordination candidate: **92/92 PASS**, 5.398 seconds, comprising
the original 40, 48 P0, 2 fixture and 2 hosting tests. Full output is in
[local regression evidence](p0-foundry/LOCAL-v8-regression.json). The earlier
80-repetition local stress result belongs to the local P0 cycle; it was not rerun
or presented as a cloud stress result here. Compilation, diff and public-artifact
checks passed; see [final local checks](p0-foundry/LOCAL-final-validation.json).

The bounded gate made **37 Hosted Responses requests**, of which 27 returned model
usage records. This includes setup failures, approval-only continuations, negative
probes and partial candidate retests; it is not a statistical evaluation. No
benchmark, dashboard, APIM, IQ, frontend, competition README rewrite, submission
media, commit or push was performed.

Remaining boundaries: deterministic in-memory `orders` fixture only; single local
AgentSession guarantees remain valid locally, but are insufficient for the hosted
scope. No cloud crash/recovery, multi-worker exactly-once or arbitrary-domain
guarantee is claimed. v8's unrepeated streaming/denial/FAILED/UNKNOWN scenarios are
NOT VERIFIED after the hosting change. A gate PASS is therefore unavailable even
apart from the demonstrated remaining concurrency failure.

## 8. Resources and cleanup

Reused: existing Foundry project/account/resource group, configured model deployment,
agent endpoint and Toolbox. Created: agent versions 7 and 8, Toolbox v4, validation
conversations/sessions, and temporary group `rg-reasonfuse-p0-validation` containing
only these four resources:

- `rfp0e7813490920` — Basic ACR, admin disabled.
- `reasonfuse-p0-env` — Container Apps environment, no Log Analytics workspace.
- `reasonfuse-p0-pull` — user-assigned pull identity, AcrPull for the temporary ACR.
- `reasonfuse-p0-operations` — minimal Operations fixture Container App.

After evidence capture, the exact group name, purpose/source/temporary tags and
four-resource inventory were checked before requesting deletion. The ten Foundry
compute sessions matched to response evidence were also deleted; nineteen other
sessions were left untouched. Agent versions and Toolbox definitions are preserved
for source review. No existing Foundry resource group was deleted.

The [final cleanup observation](p0-foundry/CLEANUP-final.json) confirms the resource
group no longer exists and all ten matched session records have status `deleted`.
The API still lists those deleted records; the field `owned_sessions_remaining`
contains tombstones, not ten running sessions.
The temporary fixture endpoint is retired after group deletion; the preserved
Toolbox definition then references a retired fixture. Further cloud work requires
recreating/repointing the fixture and resetting its state. ACTIVE agent-version
status at validation time is not a claim that the cleaned-up environment remains
ready for operational invocation.

Public JSON preserves request intent, decisions, native item types, tool calls,
responses, backend events and timings. Stable aliases replace sensitive endpoint
and session identifiers. Original captures and downloaded archives remain in the
ignored `.tools/p0-cloud/private/` directory; deployment environment files remain
ignored. Public-file hashes are listed in `evidence-manifest.json`.

**Readiness:** not ready for quantitative ON/OFF evaluation. Preserve the local
P0 result, treat v8 as an incomplete candidate, fix the real hosted ownership
boundary, then rerun the cloud gate before evaluation.

FOUNDRY CLOUD VALIDATION: FAIL
NEXT: FIX CLOUD BLOCKERS
