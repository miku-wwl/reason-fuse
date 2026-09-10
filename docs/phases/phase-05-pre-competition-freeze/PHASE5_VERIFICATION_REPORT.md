# Phase 5 Pre-Competition Freeze — Verification Report

## Scope

This verification covers the local, budget-controlled ReasonFuse Competition RC1
package. No Azure deployment, `terraform apply`, `azd provision`, or `azd deploy`
was performed. The retained Phase 4 Hosted material was audited as historical
handoff evidence and was not presented as a new live run.

The frozen profile is **15 curated scenarios × 1 repetition**, using the
deterministic local evaluator. The four Phase 4 signature demos retain their
existing three local repetitions after reset.

## Gate Results

| Gate | Result | Evidence |
|---|---|---|
| Phase 4 retained handoff | PASS | Required Phase 4 reports are present and agree on the bounded Hosted handoff. |
| Dependency freeze | PASS | `uv lock --check` passed; declared dependency versions are pinned and consistent. |
| Configuration freeze | PASS | Model, Toolbox, Knowledge Base, contract, agent versions and 15×1 scope agree between configuration and manifest. |
| Secret and tracked-file audit | PASS | No high-confidence secret pattern was found; `.azure/`, `.venv/`, `.tools/` and evidence paths are not tracked. |
| Terraform static safety | PASS | fmt, validate and refresh-free plan passed; no apply occurred. |
| Local clean build | PASS | `scripts/clean_build.ps1` exited 0 and reported `CLEAN_BUILD=PASS`. |
| Local preflight | PASS | `scripts/phase5_preflight.ps1` completed all local gates. |
| Phase 1 local regression | PASS | `tests/local_wiring.py` passed. |
| Phase 2 core regression | PASS | 36 unit tests and the temporary-root Phase 2 runner passed. |
| Phase 3 15×1 integrity | PASS | 15 valid and 15 correct runs; all five categories contain three scenarios. |
| Phase 4 retained evidence | PASS | Retained report covers Native IQ MCP, APIM, affinity, SSE, Operations, trace, rollback, cold-start and clean-start claims. |
| Recovery tooling | PASS | Local emergency recovery and demo preparation exited 0. |
| Adaptation boundary | PASS | Boundary, upgrade policy, gap template and limitations files are present and consistent. |
| Repository hygiene | PASS | No deleted experimental evaluator is referenced and no critical file is silently untracked. The two verification reports are intentional outputs of this run. |
| Repeatability | PASS | Preflight, full regression, recovery and demo checks were repeated locally without failure. |

```text
PHASE 5 RESULT: PASS
```

This is a **local RC1 verification PASS**. It does not claim that Azure is
currently deployed. The release manifest remains `READY FOR FINAL COMMIT` while
this verification output and the small evidence-isolation fix are not yet part
of a subsequent commit.

## Commands and Results

| Command | Result |
|---|---|
| `uv lock --check` | PASS, exit 0; 107 packages resolved. |
| `terraform -chdir=infra fmt -check -recursive` | PASS, exit 0. |
| `terraform -chdir=infra validate` | PASS, configuration valid. |
| `scripts/clean_build.ps1` | PASS, local-safe path; no Azure change. |
| `scripts/terraform_plan_safe.ps1` | PASS, `refresh=false`; plan `17 to add, 0 to change, 0 to destroy`; no apply. |
| `scripts/phase5_preflight.ps1` | PASS; compile, 36 unit tests, dataset, Phase 4 local preflight, manifest, fmt, validate and safe plan. |
| `scripts/run_full_regression.ps1` | PASS; local wiring, 36 tests, 15×1 suite, 10,000-event microbenchmark, Phase 4 local preflight and four signature demos. |
| `scripts/emergency_recover.ps1 -Mode local` | PASS; local fixture reset and preflight. |
| `demo/prepare_demo.ps1` | PASS; local demo prepared, Hosted mode not requested. |
| `scripts/phase2_local.py` with temporary evidence root | PASS after the isolation fix; all ten local core scenarios passed. |
| `git diff --check` | PASS; only the expected CRLF normalization warning for the generated JSON manifest remained. |

During an initial ad-hoc direct `unittest` invocation, `PYTHONPATH` was not
set and Python reported `ModuleNotFoundError: No module named 'reasonfuse'`.
This was a command-environment mistake, not a project failure. The Prompt's
corrected environment (`PYTHONPATH=src`) was then used; all 36 tests passed,
and the final `phase5_preflight.ps1` rerun also passed all unit tests.

The full local regression reported:

```text
DATASET_VALIDATION_PASS scenarios=15
PHASE3_SUITE_COMPLETE runs=15 valid=15 correct=15
MICROBENCHMARK_PASS events=10000
PHASE5_FULL_REGRESSION=PASS
```

## Phase 4 Retained Handoff

The following files were read:

- `docs/phases/phase-04-production-story/PHASE4_REPORT.md`
- `docs/phases/phase-04-production-story/PHASE4_CLOUD_VERIFICATION_REPORT.md`
- `docs/phases/phase-04-production-story/verification-report.md`

The retained handoff consistently describes the bounded Phase 4 result:

- Stable/Candidate release matrix and controlled Candidate regression;
- APIM weighted canary and session affinity;
- SSE pass-through and authoritative Operations middleware events;
- Judge Mode runtime-state projection;
- Native Foundry IQ MCP retrieval for both Hosted releases;
- retained cloud trace correlation;
- rollback/new-session Stable recovery;
- managed hosted-session cold-start evidence; and
- the fresh-environment clean-start E2E sequence.

The current repository intentionally has no live Azure resource group. The
current-turn status for live Hosted checks is therefore:

```text
HOSTED NOT RUN THIS TURN — intentional budget boundary
```

## Dependency and Configuration Freeze

The following checks passed:

- Python requirement is `>=3.13,<3.14`, with `uv.lock` constrained to Python
  3.13.
- `pyproject.toml` and `requirements.txt` use exact versions for the declared
  competition-critical packages.
- `azure.yaml` pins `azd` to `1.33.0` and uses the `gpt-5-mini` deployment at
  version `2025-08-07`.
- `config/release/competition_rc1.yaml` and the generated manifest agree on the
  15-scenario/1-repetition scope, local-safe Hosted default, runtime contract,
  Toolbox, Knowledge Base and agent version values.
- Terraform provider versions pass validation and are represented in
  `infra/.terraform.lock.hcl`.

## Secret and Tracked-File Audit

The tracked tree was inspected for high-confidence credentials, including cloud
keys, GitHub tokens, private keys, bearer values and credential-bearing storage
connection strings. No high-confidence secret pattern was found.

The only credential-related matches were expected code or documentation:

- token acquisition wording in the Phase 2 report;
- Terraform references to an Application Insights connection string; and
- telemetry code that reads the connection string from an environment variable.

No credential value was present in those matches. No `.azure/`, `.venv/`,
`.tools/` or repository evidence file is tracked. References to the deleted
experimental evaluator scripts are absent.

## Evidence Retention and Disposal

The first Phase 2 invocation exposed a project-owned defect: the documented
`REASONFUSE_EVIDENCE_ROOT` variable was ignored, so one local JSONL was written
under the repository evidence directory. That exact generated file was removed
after inspection; no repository evidence files remain.

The defect was fixed in `scripts/phase2_local.py`. The runner now uses
`REASONFUSE_EVIDENCE_ROOT` when supplied and otherwise retains its historical
repository-local default.

The corrected rerun wrote outside the repository:

```text
C:\Users\weila\AppData\Local\Temp\reasonfuse-phase5-local\phase-02-core\local-20260910\20260910T110907072334Z-local-core.jsonl
SHA256=7132DEBC39CEE7D680BFADCFA398103276832C0D3EB4199EA6428E22C755AB2D
disposal=deleted after verification
```

The Phase 3 and microbenchmark temporary directory was automatically absent
when checked after the run. No raw cloud trace, screenshot or permanent raw
JSONL was created.

## Release Manifest

The manifest generator was exercised by preflight and records:

```text
git_commit=6d68b9653a65e6aa134e53b9988428e223ea1dd9
benchmark_scenarios=15
benchmark_repetitions=1
hosted_deployment_default=false
no_implicit_azure_deploy=true
```

At report time the manifest correctly indicates a dirty working tree because
the evidence-isolation fix and these independent verification outputs are
awaiting the next intentional commit. It must not be called a final release
manifest until that commit is made and the manifest is regenerated.

## Known Limitations

- Hosted Azure resources are intentionally absent and were not recreated.
- Current-turn live APIM, Native IQ MCP, Operations, cloud trace, managed
  cold-start and clean-start E2E status is `NOT VERIFIED THIS TURN`; the
  retained Phase 4 report remains the historical handoff.
- The Phase 5 release tag was not created.
- The official competition brief was not invented; the gap-analysis document
  remains a template until the brief is available.

These are explicit budget and release-boundary decisions, not failures of the
local RC1 package.

## Phase 5 Result

```text
PHASE 5 RESULT: PASS
```

The frozen package is locally reproducible and ready for competition use after
the verification outputs and the evidence-isolation fix are committed. No
release tag or Hosted operation is authorized by this report.
