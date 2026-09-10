# Phase 4 Production Story — Independent Verification Report

## Execution scope

- Prompt: `ReasonFuse_Phase4_Production_Story_Verification_Prompt.md`
- Executed: `2026-09-10` (Pacific/Auckland)
- Source HEAD: `fbb62b107aa3513fa50a041d6b400cd4178ca7b0`
- Execution mode: budget-safe independent verification; no Azure deployment or redeployment
- Local baseline: `15 scenarios × 1 run`; signature-demo repeatability: `3 runs`
- The Verification Prompt was modified before this run and remains a local uncommitted change. The validation scripts were run with `--no-report` so construction/Hosted reports were not overwritten.

## Result summary

| Gate | Current execution | Retained prior Hosted evidence | Boundary |
| --- | --- | --- | --- |
| Phase 3 handoff | PASS | PASS | Local 15-scenario Agentathon profile |
| Stable/Candidate matrix | PASS | PASS | Matrix and controlled release metadata verified |
| APIM weighted canary | IaC PASS; live NOT VERIFIED | PASS | Azure resource group is currently absent |
| Session affinity | Local contract PASS; live NOT VERIFIED | PASS | Prior report used a real APIM client/cookie jar |
| Judge Mode runtime data | PASS | PASS | Local and prior hosted `runtime_state` projection |
| SSE pass-through | Local contract PASS; live NOT VERIFIED | PASS | Prior hosted run recorded 52 incremental chunks |
| Release lineage | PASS locally | PASS | Local trace/version projection plus prior cloud correlation |
| Native Foundry IQ MCP | NOT VERIFIED this run | PASS | Prior hosted Stable/Candidate function-call evidence retained |
| Cloud trace correlation | Local path PASS; live NOT VERIFIED | PASS | Prior bounded Log Analytics correlation retained |
| OFF/ON demo | PASS, 3/3 | PASS | Local deterministic runner |
| Unknown Correct Path | PASS, 3/3 | PASS | Local deterministic runner |
| Outcome Failure | PASS, 3/3 | PASS | Local deterministic runner |
| Candidate Regression | PASS, 3/3 | PASS | Stable fallback versus Candidate DNS repetition |
| Rollback | Local contract PASS; live NOT VERIFIED | PASS | Prior hosted new-session Stable routing evidence retained |
| Hosted cold-start | NOT VERIFIED this run | PASS | Prior official managed-session stop/resume evidence retained |
| Clean-start E2E | NOT VERIFIED this run | PASS | Prior fresh Terraform/azd run is summarized in the cloud report |

## Commands and results

### Preflight and construction-safe execution

```powershell
.venv\Scripts\python.exe scripts/phase4_production_story.py --preflight-only
.venv\Scripts\python.exe scripts/phase4_production_story.py --no-report --repetitions 3
```

Results:

- `PREFLIGHT_EXIT=0`
- `RUN_EXIT=0`
- APIM/IaC checks: `6/6 PASS`
- OTel/App Insights path checks: `4/4 PASS`
- OFF/ON: `PASS`
- Unknown Correct Path: `PASS`
- Outcome Failure: `PASS`
- Candidate Regression: `PASS`
- Local rollback contract: Stable `100` / Candidate `0`, new session `stable`

### Individual demo scripts

Each script was executed with `-Repetitions 3`. Each performs reset, preflight, scenario execution and a PASS assertion:

| Script | Result |
| --- | --- |
| `demo/run_off_on.ps1` | `PHASE4_OFF_ON_PASS` |
| `demo/run_unknown_path.ps1` | `PHASE4_UNKNOWN_PATH_PASS` |
| `demo/run_outcome_failure.ps1` | `PHASE4_OUTCOME_FAILURE_PASS` |
| `demo/run_candidate_regression.ps1` | `PHASE4_CANDIDATE_REGRESSION_PASS` |

### Static/document checks

- `phase4-manifest.json` and `release-matrix.json`: JSON parse PASS
- Phase 3 handoff: `Bounded Phase 3 result: PASS for the local 15-scenario Agentathon profile`
- `git diff --check`: PASS
- Python compilation of `src`, `scripts` and `tests`: PASS
- Azure cleanup check: `az group exists --name rg-reasonfuse-phase4c-aue` returned `false`

## Candidate regression evidence

The local independent run reproduced the intended controlled difference:

```text
Stable:    dns_resolution(INCONCLUSIVE) → service_status → PROGRESS
Candidate: dns_resolution(INCONCLUSIVE) → dns_resolution → NO_PROGRESS/STALLED
```

Both releases use the same ReasonFuse contract and the same reliability layer; only the seeded Candidate behavior differs.

## Hosted evidence boundary

The repository contains a separate retained report, [`PHASE4_CLOUD_VERIFICATION_REPORT.md`](PHASE4_CLOUD_VERIFICATION_REPORT.md), recording the earlier fresh-environment run. It reports PASS for Native IQ MCP, APIM, affinity, SSE, Operations, cloud trace, rollback, hosted cold-start and clean-start E2E.

This execution did not replay those cloud gates because the temporary resource group was intentionally removed. Therefore the current live status is `NOT VERIFIED THIS RUN`, not a new failure and not a claim that Azure is still deployed.

## Verification conclusion

```text
LOCAL INDEPENDENT VERIFICATION: PASS
RETAINED HOSTED EVIDENCE: PASS
LIVE HOSTED RE-RUN THIS TURN: NOT VERIFIED (resources intentionally absent)
PHASE 4 BOUNDED P0 STATUS: EVIDENCE-COMPLETE, RE-RUN BLOCKED BY CLEANED ENVIRONMENT
```
