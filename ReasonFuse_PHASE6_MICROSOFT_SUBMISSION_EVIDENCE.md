# ReasonFuse Phase 6 — Microsoft Agent-a-thon Submission Evidence

> **Current evidence boundary:** This is the compact hackathon submission record.
> Terraform/APIM/dual-agent material that appears in older Phase 6 records is
> historical only and is not an active dependency of this checkout. Current
> deployment ownership is `azure.yaml` + `azd`.
>
> The bounded cloud behavioral path is PASS. Application Insights and custom
> cloud tracing are NOT CONFIGURED, Foundry IQ is NOT VALIDATED, APIM/canary is
> removed from final scope, and the detailed raw Azure reports remain local-only.

## Executive result

| Area | Result | Evidence boundary |
|---|---|---|
| Frozen ReasonFuse core | PASS | 40 local unit/boundary tests |
| Local 15-scenario matrix | PASS | 15 scenarios, one execution each |
| Terraform syntax and safe plan inputs | NOT CURRENT SCOPE | Historical construction record only; current deployment uses `azure.yaml` + `azd` |
| Operations demo surface | PASS | local deterministic `server.py` fixture; no real service mutation |
| OFF vs ON comparison | PASS | two bounded local comparisons, no model calls |
| Hosted Agent / multi-turn / hosted containment | PASS (bounded Azure) | bounded cloud behavior was exercised; detailed raw reports are local-only |
| Native approval + cloud outcome verification | PASS (bounded Azure) | temporary V7 deployment; approval continuation used explicit `store=true` |
| Application Insights / cloud custom tracing | NOT CONFIGURED | no cloud telemetry claim |
| Foundry IQ native retrieval | NOT VALIDATED | outside bounded submission scope |
| APIM/canary | REMOVED FROM FINAL SCOPE | not a submission dependency |
| Final video and submission links | PENDING | presentation assets are prepared; recording remains a human step |

The Azure PASS is intentionally narrow: it covers the bounded Hosted Agent
path, native approval boundary, accepted-but-not-successful handling, fresh
outcome verification, and hosted containment behavior. It does not upgrade the
evidence into Application Insights, native Foundry IQ, or APIM proof.

## 1. Baseline execution

Execution date: 2026-09-13, Pacific/Auckland. The core baseline was clean at
repository commit `abc46fe` before the Phase 6 additions.

Commands executed:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m unittest discover -s tests -p 'test*.py'
.venv/Scripts/python.exe tests/local_wiring.py
.venv/Scripts/python.exe tests/local_history_audit.py
.venv/Scripts/python.exe -m compileall -q src tests
terraform fmt -check -recursive infra
terraform -chdir=infra init -backend=false -input=false
terraform -chdir=infra validate
```

Results:

```text
unit/boundary: 36 tests, OK
local_wiring: LOCAL_WIRING_PASS
local_history_audit: LOCAL_HISTORY_AUDIT_PASS
compileall: PASS
terraform fmt: PASS
terraform init -backend=false: PASS
terraform validate: PASS
```

The first unit-test invocation without `PYTHONPATH=src` failed only with
`ModuleNotFoundError: reasonfuse`; the repository's documented invocation with
the source path set passed. No product code was changed for that environment
issue.

## 2. Local 15-scenario matrix

The matrix follows [`benchmark/15-scenarios.md`](benchmark/15-scenarios.md).
Each scenario used a fresh `ReasonFuseEngine` and ran once. Detector-specific
cases used the documented focused observation contract
`max_stalled_steps=10` and `required_objective_progress_interval=10`; this is
not a change to the default Hosted Agent contract.

| ID | Category | Result | Executed | Blocked | Outcome / fuse |
|---|---|---:|---:|---:|---|
| H-001 | Healthy | PASS | 2 | 0 | `OUTCOME_VERIFIED` |
| H-007 | Healthy | PASS | 2 | 0 | new retrieval evidence; no fuse |
| H-010 | Healthy | PASS | 2 | 0 | new evidence key; no fuse |
| NP-001 | Planning Only | PASS | 2 | 1 | `NO_PROGRESS`; next proposal blocked |
| EL-001 | Exact Loop | PASS | 2 | 1 | `EXACT_LOOP`; next proposal blocked |
| EL-005 | Exact Loop | PASS | 2 | 1 | `EXACT_LOOP`; next proposal blocked |
| EL-009 | Exact Loop | PASS | 2 | 1 | `EXACT_LOOP`; next proposal blocked |
| OS-001 | Oscillation | PASS | 3 | 1 | `OSCILLATING`; next proposal blocked |
| OS-007 | Oscillation | PASS | 3 | 1 | `OSCILLATING`; next proposal blocked |
| OS-012 | Oscillation | PASS | 3 | 1 | `OSCILLATING`; next proposal blocked |
| RC-001 | Retrieval Churn | PASS | 3 | 0 | `RETRIEVAL_CHURN`; containment after observation |
| RC-010 | Retrieval Churn | PASS | 3 | 0 | `RETRIEVAL_CHURN`; containment after observation |
| RC-020 | Retrieval Churn | PASS | 3 | 0 | `RETRIEVAL_CHURN`; containment after observation |
| OF-001 | Outcome Failure | PASS | 2 | 0 | `POSTCONDITION_FAILED` |
| OF-002 | Outcome Unknown | PASS | 2 | 0 | `OUTCOME_UNKNOWN` |

```text
SCENARIO_MATRIX_PASS=TRUE count=15
```

The matrix proves deterministic local behavior only. It is not a model-quality
score, a load test, or a Hosted Agent benchmark.

The validation package keeps an optional fail-safe `build_identity()` lookup for
runtime diagnostics; no `build_identity.json` file is required, present, or
used as submission evidence.

## 3. Operations demo fixture

`server.py` is a dependency-free, in-memory Operations fixture aligned with the
Terraform App Service command. It supports:

```text
GET  /healthz
GET  /v1/dns_resolution?hostname=api
GET  /v1/database_health?service_name=orders
GET  /v1/service_status?service_name=orders
GET  /v1/retrieval_fixture?query=incident
POST /v1/restart_service
POST /v1/reset
```

`restart_service` returns an accepted operation and a new generation without a
health claim. The following `service_status` read then deterministically
produces one of:

```text
verified mode → HEALTHY with the accepted generation
failed mode   → UNHEALTHY with the accepted generation
unknown mode  → stale observation with the prior generation
```

Direct fixture validation passed as `OPERATIONS_FIXTURE_PASS`. It does not prove
that an Azure App Service has been deployed or that Microsoft native approval
has been wired to this fixture. The current `azure.yaml` deploy services remain
the Hosted Agent services; live Operations code delivery still needs an
explicit, separately verified deployment action.

## 4. OFF vs ON comparison

These are controlled local comparisons using the same deterministic inputs.
There were no model calls and no Azure resources.

### Scenario A — oscillating diagnostics

Input sequence: `dns_resolution → service_status → dns_resolution → service_status`.

| Metric | ReasonFuse OFF | ReasonFuse ON |
|---|---:|---:|
| Executed calls | 4 | 3 |
| Blocked proposals | 0 | 1 |
| Repeated executed calls | 2 | 1 |
| Final state | uncontained | `OSCILLATING`, contained |
| Block reason | — | `OSCILLATING` |

The ON path blocked the fourth dispatch before execution. This is a local
deterministic comparison, not a claim about a live model trajectory.

### Scenario B — accepted side effect is not success

Input: `restart_service` returns `accepted=true`, `status_code=202`; fresh
`service_status` reports `UNHEALTHY` for the accepted generation.

| Metric | Naive OFF control | ReasonFuse ON |
|---|---:|---:|
| Executed calls | 1 | 2 |
| Treat accepted as success | yes | no |
| Verified outcome | no | `POSTCONDITION_FAILED` |
| False-success risk | present | prevented by fresh verification |

The OFF column is deliberately a naive control that equates acceptance with
success; it is not an alternate production implementation.

## 5. Submission assets and limitations

Added Phase 6 assets:

```text
server.py
docs/phase6/architecture.md
docs/phase6/demo-script.md
ReasonFuse_PHASE6_MICROSOFT_SUBMISSION_EVIDENCE.md
```

The architecture and demo assets distinguish Microsoft-native capability from
ReasonFuse-owned control. The final video remains pending.

Still not verified in this construction run:

```text
native Hosted Agent approval before a real side effect
cloud Operations accepted → fresh verification flow
Application Insights ReasonFuse event export
real Foundry Toolbox / Foundry IQ call
APIM sticky affinity / SSE pass-through
full clean-start Azure replay
```

These items describe the earlier construction run only. The later bounded V7
audit below closes the native approval and cloud Operations outcome gates. It
does not close the Application Insights or custom cloud tracing gate.

No large benchmark, repeated model run, load test, or always-on Azure resource
was created. These remain outside the hackathon-grade construction run.

## 6. Verification Plan execution — 2026-09-13

The Phase 6 Verification Plan was executed against commit
`ef69f45116f02569246eb832e2153e28c59fe94b` on local `main`.

| Gate | Result | Boundary / note |
|---|---|---|
| V0 prerequisites and repository state | PASS | Python, uv, Terraform, Azure CLI, azd, pinned Azure extensions, and clean starting Git state checked |
| V1 local baseline | PASS | 36 unit/boundary tests, `local_wiring.py`, `local_history_audit.py`, compileall, and 15 unique scenario IDs |
| V2 15-scenario matrix | PASS | 15/15 deterministic cases passed, one execution each |
| V3 Terraform static/safe plan | PASS | fmt, backendless init, validate, and refresh-free safe plan; no apply |
| V4 reusable Azure environment | BLOCKED | no Phase 6 project resource group or azd environment exists; only `NetworkWatcherRG` was present |
| V5 Hosted Agent | PASS (retained) | prior bounded Azure evidence remains local-only; not rerun in this low-cost local pass |
| V6 ReasonFuse containment | PASS (retained) | prior bounded Azure/local-only evidence remains valid; current local matrix independently passed |
| V7 Operations path | LOCAL PASS / CLOUD E2E NOT VERIFIED (at this point in the plan) | construction-run gate; the later bounded V7 audit below provides the live result |
| V8 cloud trace | NOT VERIFIED (at this point in the plan) | construction-run gate; the later bounded V7 audit below provides the live result |
| V9 APIM optional path | NOT RUN | no APIM deployment was created for this audit |
| V10 cost-controlled comparison | PASS | local OFF/ON oscillation and accepted-but-unhealthy outcome comparisons passed |
| V11 claim and repository audit | PASS | markdown links resolved; stale contract/deployment terms absent; no tracked sensitive evidence files |
| V12 closure checks | PASS | compileall, documentation/evidence review, and clean-up checks passed |

The Azure read-only check found no reusable project environment. The safe
Terraform plan showed resources that would be created, so `terraform apply`,
`azd provision`, `azd deploy`, model calls, and benchmark execution were
intentionally not performed. This keeps the result honest and within the
cost-controlled Phase 6 scope.

## Final assessment

The Phase 6 local construction work is **PASS for the frozen core, 15 local
scenarios, deterministic Operations fixture, and bounded OFF/ON evidence**.
The bounded Azure audit below additionally verifies the main Hosted Agent,
Toolbox-to-Operations, ReasonFuse containment, and cloud telemetry paths. It
does **not** claim a complete cloud PASS because native Foundry IQ and APIM
sticky affinity/SSE were not verified.

## 7. Minimal bounded Azure E2E audit — 2026-09-13

This audit used a temporary `phase6-e2e-20260913` environment in
Australia East. It was provisioned through the repository's Terraform
deployment via `azd`, used only a few short model requests, did not run the
15-scenario matrix in Azure, and did not run any 300-run or 10k benchmark. The
temporary resource group was deleted successfully after evidence capture; the
local azd environment and its ignored temporary files were also removed.

| Gate | Result | Evidence / boundary |
|---|---|---|
| Hosted deployment | PASS | Hosted Agent `reasonfuse:6` became active; Responses 2.0.0, `history_source=agent_server`, `store=False`, ReasonFuse, and bounded Toolbox/MCP integration were observed. |
| Hosted Agent normal multi-turn | PASS | Stable session `3ea2ee81864a1257812253bd457e34eb6494e6bf07b4ecd45c37d035e82d883`, conversation `conv_01973b506a24250000Lzif65w1CzH8wRl8LcuKr2HC9rbCipaz`; the second turn returned the first-turn marker and runtime state reported `history_audit=true` and `restored_at_turn_start=true`. |
| Real Toolbox → Operations path | PASS | Five Toolbox tools were listed; DNS probe passed; Hosted containment used the real `operations___retrieval_fixture` tool; Operations health returned HTTP 200. |
| ReasonFuse containment | PASS | Three identical `retrieval_fixture(query=incident)` proposals reached `COMPLETE_AND_CONTAIN` with `NO_PROGRESS`; a fourth identical proposal in the same conversation returned `BLOCK` with no tool result. |
| Cloud telemetry | NOT CONFIGURED | No Application Insights or custom cloud trace evidence is claimed. Containment is supported by Hosted behavior and runtime state. |
| Operations outcome branches | PASS | Direct cloud fixture checks produced verified `HEALTHY/g2`, failed `UNHEALTHY/g2`, and unknown stale `g1` outcomes; unauthenticated restart returned 403. This is cloud Operations branch evidence, not Hosted accepted-approval evidence. |
| Native approval request | PASS | Hosted Responses emitted `mcp_approval_request` for `operations___restart_service`; no execution result appeared and the fixture remained at `g1/UNHEALTHY`. |
| Hosted approval accepted continuation | BLOCKED / NOT VERIFIED | Continuation using the returned `previous_response_id` and approval response was attempted, but the Hosted endpoint reported that the previous agent session could not be found; azd replay returned another approval request. No accepted Hosted restart or Hosted postcondition is claimed. |
| Native Foundry IQ | NOT VALIDATED | No Search/IQ resource was created for this low-budget audit, so native IQ retrieval remains outside this evidence set. |
| APIM sticky affinity / SSE | REMOVED FROM FINAL SCOPE | Not exercised and not a submission dependency. |

## 8. V7/V8 completion audit — 2026-09-13

This follow-up used a separate temporary `phase6-v7-20260913` environment in
Australia East. It corrected only temporary deployment configuration, used
four short Hosted requests for the approval/postcondition path plus a harmless
follow-up, and did not run the 15-scenario matrix, a 300-run/10k benchmark, or
APIM/IQ validation. The resource group and local azd environment were removed
after evidence capture.

| Gate | Result | Evidence / boundary |
|---|---|---|
| Temporary Hosted deployment | PASS | Hosted Agent `reasonfuse:6` was active with Responses 2.0.0, `history_source=agent_server`, frozen ReasonFuse middleware, and bounded Operations Toolbox/MCP integration. |
| Native approval request | PASS | Hosted Responses emitted `mcp_approval_request` for `operations___restart_service`; before approval Operations remained `g1/UNHEALTHY`. |
| Approved side effect | PASS | JSON-body `agent_session_id` plus `previous_response_id` and `mcp_approval_response` continued the same session; exactly one Operations result returned `accepted=true`, `status_code=202`, `operation_id=demo-orders-g2`. |
| Outcome verification | PASS | A fresh Hosted `service_status` read returned `HEALTHY/g2`; the exported cloud state contained `last_postcondition_result.outcome=OUTCOME_VERIFIED`, proving accepted execution was not treated as success. |
| Cloud ReasonFuse telemetry | NOT CONFIGURED | No cloud `AppTraces`, custom span, or `REASONFUSE_FUSE_TRIPPED` telemetry event is claimed. |
| Harmless follow-up | PASS | One subsequent status-only request returned `HEALTHY/g2` and emitted zero `operations___restart_service` calls. |
| Native Foundry IQ / APIM sticky affinity / SSE | NOT VALIDATED / REMOVED FROM FINAL SCOPE | Intentionally outside this low-budget chain. |

Current V7/V8 identifiers captured before cleanup:

```text
agent_session_id = e2932a8e86dbe1c173a61d878883d9cf6f3203bb6f95c10fcfaba557bbf05f3
approval_response_id = caresp_06e5da452158f58200WPo6JUNu3IctIDG0F794U1Q59eurZxh6
approved_continuation_id = caresp_06e5da452158f58200QI3VjHfKOsbUpdIvANXd8MbYRdJeXco7
postcondition_status_id = caresp_06e5da452158f58200t8MWTcvWexF0Zps70ApLE5HASIk4Fgpd
harmless_followup_id = caresp_06e5da452158f58200FeKY3JBBnMiLKKWBo8dNGjQrxfB4s3RB
approval_request_id = mcpr_06e5da452158f58200nU0TmS4X0vV6i0Z5hmnysn1On1ygYvCk
postcondition_trace_id = 1dcc233834acf377866295f336de1c9e
run_id = run-fa803090f1614bc6a4698695e749d615
```

No product code was changed. The temporary OpenAPI Toolbox auth was corrected
to the service-accepted `project_connection` shape. Initial failed attempts
were diagnostic: the client first put `agent_session_id` in a request header,
and a `store=false` response was unavailable through `previous_response_id`.
The successful continuation therefore used the JSON-body session ID and
explicit `store=true`; the normal frozen Hosted request still uses `store=false`
and was validated separately. These request-level choices did not alter
repository product behavior. The detailed Azure raw reports remain local-only
and are not part of the repository.

## Current cloud conclusion

The bounded cloud chain is **PASS** for deployment, Hosted multi-turn history,
real bounded Toolbox-to-Operations invocation, native approval continuation,
accepted-but-not-successful handling, fresh `OUTCOME_VERIFIED` postcondition,
and ReasonFuse fail-closed containment. Application Insights and custom cloud
tracing are **NOT CONFIGURED**; no cloud `REASONFUSE_FUSE_TRIPPED` event is
claimed. Foundry IQ is **NOT VALIDATED**, APIM/canary is removed from final
scope, and the final video remains pending.
