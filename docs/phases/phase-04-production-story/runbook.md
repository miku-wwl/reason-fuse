# Phase 4 Production Story Runbook

This runbook exercises the budget-safe local construction. It does not deploy
Azure resources, invoke GPT-5 mini, query Foundry IQ, or claim hosted PASS.

## Full construction run

From the repository root:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe scripts/phase4_production_story.py --repetitions 3
```

The command runs the four planned signature scenarios three times each and
writes only the retained construction artifacts:

- `PHASE4_REPORT.md`
- `PHASE4_OPEN_QUESTIONS.md`
- `release-matrix.json`
- `phase4-manifest.json`

Raw run records are not persisted.

## Individual demos

Each script performs local reset, static preflight, the selected demo and a
PASS/FAIL assertion:

```powershell
.\demo\run_off_on.ps1
.\demo\run_unknown_path.ps1
.\demo\run_outcome_failure.ps1
.\demo\run_candidate_regression.ps1
```

The candidate regression intentionally compares:

```text
Stable:    DNS INCONCLUSIVE -> service_status
Candidate: DNS INCONCLUSIVE -> DNS INCONCLUSIVE
           -> ReasonFuse NO_PROGRESS
```

The existing core detector is used; no Phase 2 detector or contract was
changed.

## Local versus hosted boundary

The construction can prove the local runner, version matrix, Judge Mode
projection, APIM Terraform/policy intent, affinity algorithm, SSE chunk
contract and deterministic rollback state. It cannot prove a live APIM
request, production Operations, Foundry IQ native citations, cloud trace
correlation or a platform restart. Those items remain explicitly listed in
`PHASE4_OPEN_QUESTIONS.md` for the separate Verification Prompt.

## Budget guard

Do not run `scripts/deploy.ps1` as part of this runbook. A hosted verification
pass requires a separate budget decision because fixed Azure resource charges
can exceed the cost of the 15-scenario local benchmark itself.
