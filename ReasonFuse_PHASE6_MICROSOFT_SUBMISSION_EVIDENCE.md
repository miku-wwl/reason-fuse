# ReasonFuse Phase 6 — Microsoft Agent-a-thon Submission Evidence

> Scope: bounded local construction evidence and the retained bounded Azure
> claim. This is hackathon evidence, not production certification.

## Executive result

| Area | Result | Evidence boundary |
|---|---|---|
| Frozen ReasonFuse core | PASS | 36 local unit/boundary tests |
| Local 15-scenario matrix | PASS | 15 scenarios, one execution each |
| Terraform syntax and safe plan inputs | PASS | `fmt`, `init -backend=false`, `validate`, and `refresh=false` safe plan |
| Operations demo surface | PASS | local deterministic `server.py` fixture; no real service mutation |
| OFF vs ON comparison | PASS | two bounded local comparisons, no model calls |
| Hosted Agent / multi-turn / hosted containment | PASS (retained) | bounded Azure audit was completed locally in an earlier run; detailed report is local-only and not linked or committed |
| Native approval + cloud outcome verification | CLOUD E2E NOT VERIFIED | no Operations/Toolbox deployment in this construction run |
| Application Insights / Toolbox / Foundry IQ / APIM live proof | NOT VERIFIED / OPTIONAL | no new Azure resources created |
| Final video and submission links | PENDING | presentation assets are prepared; recording remains a human step |

The retained Azure PASS is intentionally narrow: it covers the bounded Hosted
Agent path and hosted containment claim recorded by the v5.0.0 freeze. It does
not upgrade local fixture evidence into proof of Operations, native approval,
Foundry IQ, Application Insights, or APIM behavior.

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

No large benchmark, repeated model run, load test, or always-on Azure resource
was created. These remain outside the hackathon-grade construction run.

## Final assessment

The Phase 6 local construction work is **PASS for the frozen core, 15 local
scenarios, deterministic Operations fixture, and bounded OFF/ON evidence**.
Phase 6 is **not a complete cloud-verified submission** until the explicitly
listed Azure gates are either run and captured or honestly left as limitations.
