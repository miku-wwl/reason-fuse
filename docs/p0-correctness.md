# P0 operational lifecycle contract

This change applies to the existing single-agent local and Hosted Agent
compositions, using the unchanged dependency pins. Validation uses scripted
model transports, native Agent Framework approval/invocation/history layers,
and deterministic fixtures. It does not establish live Foundry acceptance.

The local-cycle results below are historical. The later Hosted correction adds
admission before session restoration: native conditional storage owns each
conversation through saved completion, and stale/uncertain continuations fail
closed. See the [v10 cloud validation report](evidence/p0-hosted-concurrency-validation.md)
for the 100-test regression result, CLOUD-1 through CLOUD-12 PASS, migration and
availability limits. This does not expand the per-object lock's own guarantee.

## Authority and concurrency scope

The supported ownership boundary is one canonical live `AgentSession` object,
used in one process and one asyncio event loop. Whole turns are serialized per
session, including native approval consumption, provider initialization,
completion verification, and history publication. Function dispatches are also
serialized per session across load, policy check, reservation, external I/O,
recording, and persistence. Concurrent tool batches therefore reload the latest
state before checking authority. Different sessions remain independent.

Locks are process-local and never enter serialized state. Cross-event-loop use
of the same live object is rejected. Serialize/restore transfers ownership only
after the previous owner stops using that session; independently restored
copies, stale snapshots, multiple workers, and concurrent requests routed to
different session objects are outside this guarantee. The hosting layer must
preserve this single-owner boundary; live Hosted Agent validation must check it.
This implementation does not provide distributed locking, crash-safe recovery,
or exactly-once execution. Losing an in-memory reservation in a process crash
cannot be repaired from an older snapshot.

## State transitions

Native Agent Framework pending requests and occurrence binding remain the sole
approval authority. A proposal records `APPROVAL_REQUIRED`; a bound denial
records `DENIED` without invoking the mutation. A rejected dispatch records
`BLOCKED`. These proposal states are separate from an already accepted action.

Before awaiting an authorized restart, the runtime increments the dispatch and
side-effect counters, reserves the postcondition slot inside both total budgets,
and persists `DISPATCHING` with action, resource, call ID, and actual tool name.
Counters count reserved attempts even when a return value never arrives.

An accepted result creates `VERIFICATION_PENDING` and a complete obligation with
action, resource, generation, accepted result, and consumption status. Only the
registered `restart_service -> service_status` read for that resource can
consume it. A concurrent sibling restart is blocked without overwriting the
accepted action or its reserved verification authority.

Verification produces `VERIFIED`, `FAILED`, or `UNKNOWN`, corresponding to
`OUTCOME_VERIFIED`, `POSTCONDITION_FAILED`, or `OUTCOME_UNKNOWN`. Both acceptance
and the fresh observation require matching nonempty generation evidence. The
observation must identify the requested resource; any supplied acceptance
resource must agree. Healthy matched output verifies; matched unhealthy or
degraded output fails; missing, malformed, stale, unavailable, or mismatched
evidence is unknown.

Cancellation, interruption, or accounting failure after reservation preserves
the attempted action as `UNKNOWN`. Restoring a persisted `DISPATCHING` action
also resolves to `UNKNOWN`. Failed and unknown outcomes contain the session and
block subsequent operational dispatch, including a newly approved retry. A
cancelled synchronous tool may still finish in its worker thread; containment
does not undo external work or infer that it did not execute.

## Completion and history

The outer completion middleware buffers the entire turn, including streaming
updates, before releasing output. If an accepted action remains unresolved, it
invokes exactly the registered read in the original tool namespace, bound to the
accepted resource, through the same core accounting middleware. It adds no
model call, uses the existing reserved slot, and applies a 10-second timeout.
A missing, ambiguous, or approval-requiring verifier yields unknown containment.
It never grants approval to a verifier or invents another verification action.

For operational sessions, all model-authored assistant answer/reasoning content
is replaced with runtime JSON describing the action, proposal, postcondition,
counter, and containment state. The structured response value is replaced too.
Native tool calls, results, approval requests, and occurrence IDs are preserved.
A denied operation therefore cannot publish fabricated success. Nonoperational
sessions retain their ordinary text. This conservative policy continues to use
runtime-owned answers for later turns in a session with an operational lifecycle.

The pinned `agent-framework-core==1.17.0` run persistence gate defers provider
history writes until the final message list has been replaced. Rejected prose
does not enter authoritative local conversation history. Exceptions drop the
deferred write and mark unresolved execution unknown. Per-service-call history
persistence is rejected before execution; remote model history remains disabled
by the existing `store=False` composition. Arbitrary custom history providers,
additional output middleware, background continuations, and service-managed
conversation state are outside this tested composition.

The gate, approval-binding reader, and parsed-response fields are private seams
in the pinned SDK. A future SDK change requires these regressions to pass again.
Streaming now trades incremental output for completion safety and buffers a
turn in memory; no new response-size or whole-model-call timeout policy is added.
This is operational outcome enforcement, not universal hallucination prevention.

## Configuration and observations

`REASONFUSE_PROFILE` defaults to `runtime`; `REASONFUSE_ENABLED` defaults to
`true`. Invalid profile, boolean, JSON, or contract limits fail during adapter
construction before credentials, model clients, or tool I/O are initialized.
Runtime rejects disabled ReasonFuse and disabled required postconditions.

Explicit `REASONFUSE_PROFILE=evaluation` permits `REASONFUSE_ENABLED=false` for
future comparisons. It also permits disabling required postconditions; accepted
execution then has no pending obligation and completion labels it
`ACCEPTED_UNVERIFIED` when enforcement is enabled. Evaluation OFF intentionally
does not enforce runtime completion or containment. A persisted disabled session
cannot resume in runtime; evaluation preserves its disabled flag even if the
environment says enabled. Persisted contract limits remain immutable on resume.

`read_reasonfuse_state` exposes authoritative enabled/profile/contract and
lifecycle state, including after containment. Correctness code uses independent
runtime telemetry and does not import synthetic validation state. Existing
validation helpers remain in the compositions; no broad profile refactor occurs.

World observations merge stable fields by resource. Discovering a field or
changing a known value/generation counts once; alternating unchanged partial
service/database views does not repeatedly count as progress. Todo deltas remain
separate, and retrieval evidence retains its existing semantics.

Reset is absent from the cloud MCP inventory, Hosted Toolbox allowlist, and
approval map. The cloud fixture exposes out-of-band `POST /test/reset`; the
local fixture retains its existing `/v1/reset` harness helper. Neither is an
agent-exposed mutation. The only exposed external mutation is the registered
restart operation. Fixture administration assumes trusted test setup and is not
a production administration API.

## Deterministic validation commands

Run from the repository root in PowerShell with the existing environment:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test*.py'
.\.venv\Scripts\python.exe -B tests/local_wiring.py
.\.venv\Scripts\python.exe -B tests/local_history_audit.py
git diff --check
```

`tests/test_p0_runtime.py` uses scripted transport responses under native
framework approval, concurrent invocation, streaming, and persistence. Its
mutation counter deliberately has no backend duplicate rejection.
`tests/test_p0_contracts.py` covers startup policy, verifier contracts, stable
world observations, diagnostics, inventory, fixture reset, and both adapter
compositions. Existing tests remain; old expectations that allowed database
health to consume a restart obligation or omitted required generation are
updated to the corrected contract.

## Executed checks for this change

On 2026-09-20 (Pacific/Auckland), Python 3.13.9 and the unchanged installed pins:

| Check | Result |
| --- | --- |
| Full unittest discovery | PASS: 88 tests, 5.420 seconds; 40 retained existing tests and 48 new tests |
| Four concurrency/cancellation regressions repeated 20 times | PASS: 80 additional executions, 4.314 seconds |
| Compilation of every repository Python source using `compile()` | PASS: 34 files |
| Existing local wiring script | PASS |
| Existing local history audit script | PASS |
| JSON session/history round trips, native approval restoration, rejected prose exclusion | PASS in the full suite |
| Both adapter compositions and actual Hosted server history configuration, using scripted transport | PASS in the full suite |
| Installed project dependency pin comparison | PASS: all 10 dependencies |
| Azure manifest YAML parsing and tool/approval inventory | PASS |
| `git diff --check` and whitespace scan including new files | PASS: 20 changed/new files |
| Existing static/type/lint command | Not applicable: no separate checker is configured in this repository |
| Live model, Azure/Foundry hosting, distributed ownership and persistence | NOT VERIFIED; outside this cycle |

No deployment, SDK upgrade, benchmark report, competition README/package edit,
commit, or push was performed. Historical evidence was left intact.

## Changed files

- `src/reasonfuse/core/engine.py`, `middleware.py`, `outcome.py`, `provider.py`, `state.py`
- `src/reasonfuse/completion.py`, `runtime.py`, `config.py`, `telemetry.py` (new)
- `src/reasonfuse/agent.py`, `local_runtime.py`
- `azure.yaml`, `cloud/operations-mcp/server.py`, `cloud/operations-mcp/README.md`
- `tests/test_p0_runtime.py`, `tests/test_p0_contracts.py`, `tests/p0_support.py` (new)
- `tests/unit/test_core.py`, `tests/unit/test_core_boundaries.py`
- `docs/p0-correctness.md` (new)
