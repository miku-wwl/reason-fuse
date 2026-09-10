# ReasonFuse Phase 5 — Pre-Competition Freeze Verification Prompt

> Purpose: independently verify the budget-controlled ReasonFuse Competition RC1 package before the Microsoft Agentathon submission.
> Audience: independent validation agent
> Phase: 5 — Pre-Competition Freeze
> Role: local release validator
> Prerequisite: Phase 4 = BOUNDED P0 PASS or PASS
> Primary Exit Gate: local frozen package PASS + reproducible local checks + retained Phase 4 handoff consistent

---

# 0. Repository and scope handoff

The repository uses this root-level prompt:

~~~
D:\workshop\sep\reason-fuse\ReasonFuse_Phase5_PreCompetition_Freeze_Verification_Prompt.md
~~~

The nested _Phase5\_PreCompetition\_Freeze\_Verification\_Prompt.md path is
not a tracked file in the current repository. Do not create a duplicate prompt
tree for it.

The construction handoff is:

~~~
docs/phases/phase-05-pre-competition-freeze/PHASE5_REPORT.md
docs/phases/phase-05-pre-competition-freeze/release-manifest.json
docs/phases/phase-05-pre-competition-freeze/COMPETITION_UPGRADE_POLICY.md
docs/phases/phase-05-pre-competition-freeze/RECOVERY_RUNBOOK.md
docs/phases/phase-05-pre-competition-freeze/COMPETITION_ADAPTATION_BOUNDARY.md
docs/phases/phase-05-pre-competition-freeze/KNOWN_LIMITATIONS.md
~~~

Do not overwrite PHASE5_REPORT.md. It is the construction report. Write the
independent result to:

~~~
docs/phases/phase-05-pre-competition-freeze/PHASE5_VERIFICATION_REPORT.md
docs/phases/phase-05-pre-competition-freeze/PHASE5_VERIFICATION_OPEN_QUESTIONS.md
~~~

The frozen competition profile is:

~~~
15 curated benchmark scenarios × 1 repetition
deterministic LocalEvaluator
local-safe default commands
one-time Hosted evidence retained from Phase 4
no implicit Azure deployment
~~~

This is a budget-controlled competition package. Verification must not increase
benchmark scope, add provider calls, or create a new infrastructure obligation.

---

# 1. Non-negotiable safety boundary

The following commands are forbidden in this verification unless the user
explicitly authorizes a separate Hosted operation:

~~~
terraform apply
azd provision
azd deploy
scripts/clean_build.ps1 -DeployHosted
scripts/phase5_preflight.ps1 -Hosted
~~~

The default validation must not modify Azure resources or incur Azure charges.
Use:

~~~
scripts/clean_build.ps1
scripts/phase5_preflight.ps1
scripts/run_full_regression.ps1
scripts/emergency_recover.ps1 -Mode local
~~~

The Phase 4 Hosted report may be checked for consistency, but it is not a
reason to redeploy Azure during Phase 5.

---

# 2. Validation result

Return this table in the verification report:

~~~
Phase 4 retained handoff       PASS / FAIL
Dependency freeze              PASS / FAIL
Configuration freeze           PASS / FAIL
Secret and tracked-file audit  PASS / FAIL
Terraform static safety        PASS / FAIL
Local clean build              PASS / FAIL
Local preflight                PASS / FAIL
Phase 1 local regression       PASS / FAIL
Phase 2 core regression        PASS / FAIL
Phase 3 15×1 integrity         PASS / FAIL
Phase 4 retained evidence      PASS / FAIL
Recovery tooling               PASS / FAIL
Adaptation boundary            PASS / FAIL
Repository hygiene             PASS / FAIL
Repeatability                  PASS / FAIL

PHASE 5 RESULT:
PASS / BLOCKED
~~~

PASS means the local RC1 package is ready for competition use. It does not
claim that Azure resources are currently deployed.

---

# 3. Phase 4 handoff audit

Read:

~~~
docs/phases/phase-04-production-story/PHASE4_REPORT.md
docs/phases/phase-04-production-story/PHASE4_CLOUD_VERIFICATION_REPORT.md
docs/phases/phase-04-production-story/verification-report.md
~~~

Confirm that the retained Phase 4 result supports:

~~~
Stable/Candidate
APIM canary and affinity
SSE
Operations
Judge Mode runtime data
Candidate regression
rollback and new-session Stable recovery
clean-start Hosted evidence
~~~

Record this as a retained-evidence handoff. Do not label it as a new live run.
The absence of current Azure resources is an intentional budget boundary, not a
local implementation failure.

---

# 4. Dependency and configuration freeze

Inspect:

~~~
pyproject.toml
uv.lock
requirements.txt
infra/.terraform.lock.hcl
azure.yaml
config/release/competition_rc1.yaml
docs/phases/phase-05-pre-competition-freeze/release-manifest.json
~~~

Confirm:

~~~
no floating competition-critical dependency was introduced
Python/model/Toolbox/Knowledge Base/Run Contract values agree
Stable and Candidate versions agree with the manifest
Terraform provider versions agree with the lock file
benchmark_scenarios = 15
benchmark_repetitions = 1
hosted_deployment_default = false
no_implicit_azure_deploy = true
~~~

Run the available local consistency checks:

~~~powershell
uv lock --check
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra validate
~~~

If the manifest says working_tree_dirty = true, do not call it a final release
manifest. Record it as READY FOR FINAL COMMIT.

---

# 5. Secret and tracked-file audit

Inspect tracked files and generated Phase 5 documents for accidental:

~~~
API keys
access tokens
passwords
private certificates
unredacted Authorization values
connection strings containing credentials
temporary Azure environment files
raw cookies
~~~

The following are allowed when they are code or redacted examples:

~~~
credential acquisition calls
environment variable names
fake/invalid example values
redaction logic
hashes and nonsecret version identifiers
~~~

Also confirm:

~~~
.azure/, .venv/, .tools/ and temporary run directories are not tracked
no deleted experimental evaluator is referenced
no critical Phase 5 file is silently untracked
~~~

Record Secret and tracked-file audit = PASS only after inspecting the actual
working tree.

---

# 6. Terraform and local build safety

Run:

~~~powershell
.\scripts\clean_build.ps1
~~~

This must remain local-safe. It may run dependency synchronization, Terraform
initialization without a backend, Terraform validation and local preflight. It
must not run terraform apply, azd provision or azd deploy.

Run the explicit safe plan:

~~~powershell
.\scripts\terraform_plan_safe.ps1
~~~

Required interpretation:

~~~
PASS = plan was generated with refresh=false and no apply occurred
NOT VERIFIED = live Azure state was not queried
~~~

NOT VERIFIED for live state is expected in this budget-controlled phase.

---

# 7. Local preflight and regression

Run:

~~~powershell
.\scripts\phase5_preflight.ps1
.\scripts\run_full_regression.ps1
~~~

The local regression must cover:

~~~
Python compilation
unit tests
local wiring
15-scenario dataset validation
15×1 benchmark suite
10,000-event local microbenchmark
Phase 4 local preflight
local signature demos
~~~

No cloud call is required for this gate.

For an additional deterministic core check, use a temporary output root:

~~~powershell
$env:REASONFUSE_EVIDENCE_ROOT = Join-Path $env:TEMP 'reasonfuse-phase5-local'
$env:PYTHONPATH = 'src'
.venv\Scripts\python.exe scripts\phase2_local.py
~~~

Do not write new raw evidence into a repository evidence directory. Keep any
temporary output outside the repository and remove it after the report records
the result.

---

# 8. Phase 1 and Phase 2 local gates

Confirm the local results cover these architecture-critical invariants:

~~~
history/session behavior
Toolbox BEFORE/AFTER interception
blocked action has zero side effect
approval allow and deny behavior
exact loop containment
oscillation containment
retrieval churn containment
useful recheck preservation
todo-only progress is not objective progress
accepted action is not outcome success
Run Contract counters
outcome success/failure/unknown handling
~~~

Use the existing 36 unit tests, tests/local_wiring.py and the local Phase 2
runner. Do not start a Hosted Agent merely to recreate an already retained
earlier phase result.

---

# 9. Phase 3 evidence integrity

Verify the canonical local package:

~~~
benchmark/datasets/reasonfuse_v2.jsonl
benchmark/datasets/schema.json
benchmark/datasets/frozen_thresholds.json
benchmark/PHASE3_REPORT.md
docs/phases/phase-03-evidence-benchmark/verification-report.md
~~~

Required:

~~~
15 unique scenarios
3 scenarios per category
1 repetition per scenario
15 valid runs
confusion matrix is reproducible
OFF/ON comparison is present
microbenchmark is present
no provider call is required
~~~

Raw run JSONL may be generated in a temporary directory for independent
recalculation. A temporary run does not need to become a permanent repository
artifact.

If the current Phase 5 change altered core behavior, rerun the 15×1 suite. If
only scripts or Markdown changed, record that the existing Phase 3 result
remains attributable to the unchanged core.

---

# 10. Phase 4 evidence boundary

Do not run a new Hosted Phase 4 campaign in this prompt.

Check only that:

~~~
the retained Phase 4 reports are present
the reports agree with the release manifest
the current local code does not falsely claim live Azure availability
the default scripts are fail-closed for Hosted deployment
~~~

Current Azure resources being absent must be reported as:

~~~
HOSTED NOT RUN THIS TURN — intentional budget boundary
~~~

Do not convert that status into a Phase 5 failure when all local gates pass.

---

# 11. Demo, recovery and runbook checks

Run:

~~~powershell
.\scripts\emergency_recover.ps1 -Mode local
.\demo\prepare_demo.ps1
~~~

Confirm:

~~~
local reset returns a clean fixture
local preflight passes
the four signature demos remain executable
the recovery command is non-destructive
the runbook commands match the actual scripts
~~~

The retained three-repeat local signature result may be used as supporting
evidence. Do not add another repetition campaign unless a failed local check
requires it.

---

# 12. Evidence retention policy

The canonical Phase 5 evidence package is documentation-first:

~~~
Phase 1 verification report
Phase 2 report and verification report
Phase 3 report and verification report
Phase 4 retained Hosted summary
Phase 5 construction report
Phase 5 verification report
Phase 5 open-questions report
release manifest
upgrade policy
recovery runbook
adaptation boundary
known limitations
~~~

Do not require screenshots, raw cloud traces or permanent raw JSONL when Azure
is intentionally absent. If a temporary local run is used, record its path,
hashes and disposal decision in the verification report, then remove it.

Do not recreate deleted exploratory evidence merely to satisfy an old prompt.

---

# 13. Competition adaptation and hygiene

Inspect:

~~~
COMPETITION_ADAPTATION_BOUNDARY.md
COMPETITION_GAP_ANALYSIS_TEMPLATE.md
COMPETITION_UPGRADE_POLICY.md
KNOWN_LIMITATIONS.md
~~~

Confirm:

~~~
the official brief has not been guessed before publication
presentation changes are separated from runtime changes
a behavioral change requires a regression rerun
the 15×1 baseline remains intact
no stale deployment command runs implicitly
no critical file is untracked
~~~

The gap-analysis file is a template until the official brief is available. Do
not invent competition requirements to fill it.

---

# 14. Repeatability and final manifest

Repeat only the cheap local checks that can reveal nondeterminism:

~~~powershell
.\scripts\phase5_preflight.ps1
.\scripts\run_full_regression.ps1
~~~

If the second local run fails, record the exact failure and stop. Do not deploy
Azure to hide a local reproducibility problem.

After the working tree is intentionally finalized:

~~~powershell
$env:PYTHONPATH = 'src'
.venv\Scripts\python.exe scripts\write_phase5_release_manifest.py
git diff --check
git status --short
~~~

The final manifest must report:

~~~
working_tree_dirty = false
15 scenarios / 1 repetition
hosted deployment default = false
no implicit Azure deployment
canonical file hashes match the final commit
~~~

Do not create a release tag in this validation unless the user explicitly
authorizes the final release operation after reviewing the report.

---

# 15. Verification report format

Write:

~~~
docs/phases/phase-05-pre-competition-freeze/PHASE5_VERIFICATION_REPORT.md
~~~

Include:

~~~markdown
# Phase 5 Pre-Competition Freeze — Verification Report

## Scope
Local budget-controlled RC1; no Azure deployment this turn.

## Gate Results
<the result table from Section 2>

## Commands and Results
<commands, exit codes, and concise outputs>

## Phase 4 Retained Handoff
<what was reused and what was not rerun>

## Evidence Retention
<temporary paths, hashes and disposal decisions>

## Release Manifest
<commit, dirty state, and scope values>

## Known Limitations
<only current, observed limitations>

## Phase 5 Result
PASS / BLOCKED
~~~

Write unresolved items separately:

~~~
docs/phases/phase-05-pre-competition-freeze/PHASE5_VERIFICATION_OPEN_QUESTIONS.md
~~~

Use NOT VERIFIED only for live/platform checks intentionally excluded by this
budget boundary. Do not list those exclusions as unfinished implementation work.

---

# 16. PASS gate

Return:

~~~
PHASE 5 RESULT: PASS
~~~

only when all mandatory local conditions are true:

~~~
[ ] Phase 4 retained handoff is consistent
[ ] dependencies are pinned and locally consistent
[ ] release manifest values match the repository
[ ] secret/tracked-file audit passes
[ ] Terraform fmt/validate and safe plan pass
[ ] local clean build passes
[ ] local preflight passes
[ ] Phase 1/2 local regression passes
[ ] Phase 3 15×1 evidence is reproducible
[ ] Phase 4 reports are not falsely represented as live this turn
[ ] local recovery tooling passes
[ ] runbook and adaptation boundary match the repository
[ ] repository hygiene passes
[ ] repeat local regression is consistent
[ ] independent verification report and open-questions report are written
~~~

The release tag is not required for the verification PASS. It is a separate,
user-authorized release operation after review.

---

# 17. BLOCKED gate

Return:

~~~
PHASE 5 RESULT: BLOCKED
~~~

if any of these occurs:

~~~
local clean build fails
local preflight fails
core regression fails
15×1 evidence cannot be recomputed
manifest contradicts the repository
secret is exposed
recovery command is destructive or broken
critical file is missing or untracked
verification report cannot explain the final state
~~~

Do not block solely because Azure is currently absent, screenshots were not
captured, or old raw exploratory evidence was intentionally deleted.

---

# 18. Final instruction

This verification freezes the existing hackathon package. It must leave the
project with:

~~~
one local reproducible build
one fixed 15×1 benchmark profile
one retained Phase 4 Hosted handoff
one documented recovery path
one independent Phase 5 verification report
one separate open-questions report
~~~

Do not expand the architecture or the validation budget during this phase.
