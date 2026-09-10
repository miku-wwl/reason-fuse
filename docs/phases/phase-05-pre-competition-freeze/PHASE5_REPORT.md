# Phase 5 Pre-Competition Freeze Report

## Release Candidate

- Name: `ReasonFuse Competition RC1`
- Proposed tag: `reasonfuse-competition-rc1`
- Release manifest: `release-manifest.json`
- Tag status: **NOT CREATED**; construction must not self-authorize the tag

## Architecture

**UNCHANGED.** Phase 5 adds freeze, recovery and reproducibility tooling only.

## Dependency Freeze

**PASS — construction audit.** `pyproject.toml`, `uv.lock`, `requirements.txt` and
`infra/.terraform.lock.hcl` are the declared sources of truth. Exact versions
are recorded in the release configuration and manifest.

## Terraform / `azure.yaml` Freeze

**PASS — construction audit.** Terraform provider versions and the `azure.yaml` runtime/model
configuration are retained. The default clean-build path performs no Azure
provisioning.

## Local Preflight and Regression

**PASS.** The following entry points are provided and exercised:

- `scripts/phase5_preflight.ps1`
- `scripts/clean_build.ps1`
- `scripts/run_full_regression.ps1`
- `demo/prepare_demo.ps1`
- `scripts/emergency_recover.ps1`

`scripts/phase5_preflight.ps1` passed compile, unit, dataset, Phase 4 local,
manifest, Terraform fmt, Terraform validate and refresh-free Terraform plan.
The safe plan was `17 to add, 0 to change, 0 to destroy`; it did not apply.

## Signature Demo

**PASS — local regression.** The Phase 4 four-demo runner remains the frozen
local path and passed three repetitions after reset for each signature demo.

## Benchmark Evidence Preservation

**PASS — bounded local package.** The canonical Phase 3 report, dataset,
thresholds and reproducible commands are retained. The 15×1 suite produced 15
valid/correct records and the 10,000-event microbenchmark passed in a temporary
run directory; raw run directories remain disposable by design.

## Judge Mode Freeze

**PASS — construction audit.** Existing runtime fields and responsibility boundaries remain frozen;
Phase 5 does not redesign the UI or add a second enforcement engine.

## Recovery Scripts and Runbook

**PASS.** See `RECOVERY_RUNBOOK.md` and `scripts/emergency_recover.ps1`. The
local prepare and recovery commands both returned exit code zero.

## Competition Adaptation Boundary

**PASS.** See `COMPETITION_ADAPTATION_BOUNDARY.md`.

## Known Limitations

See `KNOWN_LIMITATIONS.md`. In particular, Hosted resources are intentionally
absent and must not be represented as a fresh live PASS.

## Architecture Change Required?

**NO.**

## Phase 5 Result

```text
PHASE 5 CONSTRUCTION COMPLETE
READY FOR INDEPENDENT VALIDATION
```

This report does not self-award Phase 5 PASS and does not authorize a release
tag.

## Executed construction checks

```text
36 unit tests                         PASS
dataset validation (15 scenarios)     PASS
Terraform fmt / validate              PASS
Terraform plan (refresh=false)        PASS: 17 add / 0 change / 0 destroy
Phase 4 local preflight               PASS
Phase 4 signature regression (3x)     PASS
Phase 3 suite (15x1)                  PASS: 15 valid / 15 correct
microbenchmark                        PASS: 10,000 events
clean_build.ps1                       PASS: local-safe
prepare_demo.ps1                      PASS
emergency_recover.ps1 -Mode local    PASS
Hosted deployment                     NOT RUN: no Azure resources requested
```
