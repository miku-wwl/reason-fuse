# ReasonFuse Phase 5 — Pre-Competition Freeze Verification Prompt

> **Purpose:** Independently verify that ReasonFuse is frozen, reproducible, recoverable, and safe to carry into competition day without further architecture work.  
> **Audience:** GPT-6 Astra / independent validation agent  
> **Phase:** 5 — Pre-Competition Freeze  
> **Role:** Final release validator  
> **Prerequisite:** Phase 4 = PASS  
> **Primary Exit Gate:** `clean-start full-chain PASS twice + frozen release reproducible + evidence/recovery package complete`

---

# 1. Mission

This is the final pre-competition release validation.

Your job is to determine whether ReasonFuse can be treated as a frozen competition-ready release.

Do not reward feature count.

Do not approve because previous phases passed.

Revalidate the frozen build from a clean state.

Return:

```text
Dependency Freeze           PASS / FAIL
Config Freeze               PASS / FAIL
Terraform / azd             PASS / FAIL
Secret Audit                PASS / FAIL
Clean Build                 PASS / FAIL
Preflight                   PASS / FAIL
Phase 1 Critical Regression PASS / FAIL
Phase 2 Core Regression     PASS / FAIL
Phase 3 Evidence Integrity  PASS / FAIL
Phase 4 Production Regression PASS / FAIL
Signature Demo              PASS / FAIL
Recovery                    PASS / FAIL
Evidence Package            PASS / FAIL
Adaptation Boundary         PASS / FAIL
Repeatability               PASS / FAIL

PHASE 5 RESULT:
PASS / BLOCKED
```

---

# 2. Final Validation Principles

## Principle 1 — No New Features During Validation

Do not add features to make validation pass.

Allowed:

```text
small bug fix
script fix
config correction
missing pin
documentation correction
```

Any functional behavior change requires affected regression tests to rerun.

---

## Principle 2 — Clean State Matters

A system that only works because a developer shell has hidden state is not frozen.

Validation must include clean-start reproduction.

---

## Principle 3 — Evidence Must Survive Environment Failure

The project must retain enough:

```text
raw benchmark data
screenshots
traces
release metadata
reports
```

to prove the project even if a live Azure dependency becomes temporarily unavailable.

---

## Principle 4 — Architecture Reopening Is Exceptional

Only a proven frozen architectural assumption failure may reopen architecture.

Ordinary script, SDK, Terraform, or UI bugs do not justify redesign.

---

# 3. Pre-Validation Inventory

Record:

```text
date/time
git commit

proposed release name
proposed release tag

stable agent version
candidate agent version

model version
prompt version
toolbox version
knowledge base version
reasonfuse contract version
dataset version

Python version
azd version
Terraform version
AzureRM version
AzAPI version

Agent Framework version
Foundry hosting version
azure-ai-projects version
```

Compare these with the frozen release manifest.

Any unexplained mismatch:

```text
Config Freeze = FAIL
```

---

# 4. Dependency Freeze Audit

Inspect:

```text
pyproject.toml
uv.lock
requirements.txt
```

Confirm competition-critical dependencies are exact.

Search for floating specs:

```text
>=
latest
*
unbounded compatible ranges
```

Document any unavoidable exception.

Check installed environment against lock files.

Required:

```text
installed versions match frozen manifest
```

---

# 5. Upgrade Policy Audit

Verify a competition-window freeze policy exists.

It must explicitly prevent casual upgrades of:

```text
Agent Framework
Foundry hosting
azure-ai-projects
Terraform providers
model
Toolbox
knowledge base
```

unless a blocking defect requires it.

---

# 6. Configuration Source-of-Truth Audit

Confirm one clear frozen manifest exists.

Verify:

```text
agent versions
model
prompt
Toolbox
KB
ReasonFuse contract
dataset
APIM weights
dependencies
```

match the deployed system.

No conflicting duplicate config should claim to be current.

---

# 7. Secret Audit

Search repository and generated evidence.

Look for:

```text
API keys
tokens
passwords
connection strings
Authorization headers
private certs
secret query strings
```

Also inspect:

```text
logs
screenshots metadata where practical
raw HTTP dumps
evidence files
```

Any exposed real secret:

```text
Secret Audit = FAIL
```

Rotate if necessary.

---

# 8. Terraform Validation

Run:

```text
terraform fmt -check
terraform validate
terraform plan
```

Record:

```text
exit codes
provider versions
unexpected drift
```

The plan should not reveal accidental destructive changes.

Document expected external Foundry/data-plane assets managed outside Terraform.

---

# 9. `azure.yaml` Validation

Inspect actual deployment configuration.

Confirm:

```text
Responses protocol 2.0.0
remote build
runtime
entry point
Hosted Agent config
```

matches frozen documentation.

---

# 10. Clean Build Test — First Pass

Use the documented clean-build procedure.

Required:

```text
fresh dependency install
infra validation/provision
agent deployment
Toolbox verification
preflight
```

Do not manually patch source during the run.

Record all commands and failures.

At completion:

```text
Clean Build Pass 1 = PASS / FAIL
```

---

# 11. Preflight Validation

Run the frozen preflight.

Required checks:

```text
auth
RBAC
Stable endpoint
Candidate endpoint
Responses endpoint
Toolbox
tools/list
Operations API
AgentSession smoke
Function Middleware interception
R2 approval smoke
APIM endpoint
affinity
SSE
tracing
Application Insights
Judge Mode backend
```

A required failure blocks Phase 5.

---

# 12. Phase 1 Critical Regression

Revalidate architecture-critical assumptions.

Required:

```text
history_source="agent_server"
multi-turn history works
AgentSession state survives
store=False path remains correct
no duplicate canonical history

Toolbox BEFORE/AFTER interception
pre-execution BLOCK
blocked tool execution count = 0

R2 approval pause
approve exact action
deny
state survives

APIM affinity
SSE streaming
```

Any architecture-critical failure:

```text
Phase 1 Critical Regression = FAIL
```

Then classify whether architecture unfreeze is required.

---

# 13. Phase 2 Core Regression

Run the frozen core regression.

Required:

```text
OFF baseline
ON containment
Exact Loop
Oscillation
Retrieval Churn
Useful Recheck
Todo-only progress negative control
Run Contract
Outcome success
Outcome failure
```

Required invariants:

```text
Todo Delta alone != Objective Progress

Execution accepted != Outcome success
```

---

# 14. Phase 3 Evidence Integrity

Verify frozen evidence exists.

Required:

```text
100 scenarios
300 valid runs
raw JSONL
normalized results
confusion matrix
metrics
microbenchmark
PHASE3_REPORT.md
```

Independently recompute headline metrics from raw data.

At minimum:

```text
TP
FP
TN
FN
Recall
Precision
FPR
FNR
Healthy Completion
Useful Recheck Preservation
Postcondition Failure Detection
```

If numbers no longer match:

```text
Phase 3 Evidence Integrity = FAIL
```

---

# 15. Benchmark Rerun Policy Check

Determine whether Phase 5 changed:

```text
detector logic
Run Contract
progress semantics
Outcome Verifier semantics
tool normalization
retrieval normalization
```

If YES:

```text
full 300-run benchmark must have been rerun
```

If not rerun:

```text
Phase 5 = BLOCKED
```

---

# 16. Microbenchmark Integrity

Verify the frozen 10,000-event microbenchmark result remains attributable to the current commit.

If core code changed since the benchmark:

```text
rerun microbenchmark
```

Record:

```text
throughput
p50
p95
p99
```

---

# 17. Phase 4 Production Regression

Revalidate:

```text
Stable/Candidate exist
same controlled dependencies
APIM weighted pool
session affinity
Judge Mode client affinity
SSE
release lineage
Foundry tracing
Application Insights
Candidate Regression
rollback
Stable recovery
```

---

# 18. Judge Mode Integrity

Run Judge Mode live.

Confirm displayed values come from real runtime state.

Required:

```text
Safety
Authorization
ReasonFuse
Trajectory
Objective Progress
Evidence Delta
World-State Delta
Retrieval Delta
Todo Delta
Postcondition Delta
Useful Recheck
Fuse reason
containment latency
release role
```

Check:

```text
Planning changed. Reality did not.
```

is used only when the data supports it.

---

# 19. Signature Demo Validation

Run:

```text
A — OFF / ON
B — Unknown Correct Path
C — Outcome Failure
D — Candidate Regression
```

Each scenario must be reset before execution.

Required:

```text
3 consecutive PASS executions each
```

Record evidence.

---

# 20. Clean-Start Full Chain — First Pass

From a clean operational state execute:

```text
clean build
↓
preflight
↓
OFF/ON
↓
Unknown Correct Path
↓
Outcome Failure
↓
Candidate Regression
↓
rollback
↓
Stable recovery
```

No source edits.

No hidden manual repair.

Result:

```text
FULL CHAIN PASS 1
```

or FAIL.

---

# 21. Recovery Script Validation

Test the documented safe recovery path.

Examples:

```text
restore APIM weights
restore frozen agent version
rerun preflight
```

Do not deliberately destroy production resources.

Simulate or safely induce only non-destructive recoverable states.

Required:

```text
recovery command works
system returns to frozen expected state
```

---

# 22. Recovery Runbook Audit

Inspect:

```text
RECOVERY_RUNBOOK.md
```

It should cover:

```text
agent unavailable
Toolbox unavailable
APIM routing wrong
affinity lost
SSE issue
Judge Mode issue
trace ingestion delay
Candidate not removed
dirty scenario state
deployment drift
```

Each entry should contain:

```text
symptom
check
safe action
verification
```

---

# 23. Backup Evidence Audit

Confirm preserved evidence exists for each signature demo.

At minimum:

```text
Judge Mode screenshot
trace evidence
raw run result
release role
tool sequence
ReasonFuse decision
Outcome result where relevant
```

These assets must remain usable if live demo becomes temporarily unavailable.

---

# 24. Frozen Benchmark Package Audit

Confirm raw evidence was not overwritten.

Check:

```text
immutable/frozen copy
dataset version
report version
release manifest reference
```

A summary without raw evidence is insufficient.

---

# 25. Competition Adaptation Boundary Audit

Inspect:

```text
COMPETITION_ADAPTATION_BOUNDARY.md
```

Allowed post-brief changes should be limited to:

```text
prompt
scenario
runbooks
tool descriptions
Judge Mode copy
demo story
benchmark subset
README / pitch
domain mapping
```

Core redesign should remain explicitly outside normal adaptation.

---

# 26. Gap-Analysis Template Audit

Verify:

```text
COMPETITION_GAP_ANALYSIS_TEMPLATE.md
```

contains:

```text
Official Requirement
Current Coverage
Gap
Required Change
Architecture Impact
Estimated Hours
Risk
Decision
```

It should be ready to use immediately when the brief is published.

---

# 27. Known-Limitations Audit

Inspect:

```text
KNOWN_LIMITATIONS.md
```

Confirm:

```text
real limitations are listed
resolved limitations are removed or marked resolved
no critical issue is hidden
```

Do not fail Phase 5 merely because non-critical limitations exist.

Fail only if a known critical limitation invalidates the competition build.

---

# 28. Repository Hygiene Audit

Check:

```text
main branch/current path clearly reflects frozen architecture
no stale experimental config can accidentally deploy
no alternate active Terraform state path
no accidental debug mode
no stale Candidate behavior injected into Stable
no untracked critical files
```

---

# 29. Clean Build Test — Second Independent Pass

Repeat the clean-start procedure a second time.

Prefer:

```text
new shell/session
fresh local virtual environment
fresh generated state where practical
```

Do not rely on the first run's process state.

Required:

```text
Clean Build Pass 2 = PASS
```

---

# 30. Clean-Start Full Chain — Second Pass

Repeat:

```text
preflight
OFF/ON
Unknown Correct Path
Outcome Failure
Candidate Regression
rollback
Stable recovery
```

Required:

```text
FULL CHAIN PASS 2
```

This second full-chain pass is mandatory.

---

# 31. Repeatability Gate

Phase 5 requires:

```text
clean-start full-chain PASS twice
```

The two passes must not depend on source edits between them.

If the second pass requires a code change:

```text
fix
reset validation count
run two clean passes again
```

---

# 32. Release Manifest Final Audit

After all tests pass, verify the release manifest one final time.

The manifest must exactly match:

```text
deployed versions
git commit
dependencies
dataset
contract
APIM state
```

---

# 33. Release Tag Authorization

Only now may the validator authorize a release tag.

Recommended:

```text
reasonfuse-competition-rc1
```

If a tag already exists on a non-validated commit:

```text
do not reuse it
```

Create a new deterministic release tag.

---

# 34. PHASE5_REPORT.md

Update with real evidence:

```text
# Phase 5 Pre-Competition Freeze Validation Report

## Release Candidate
...

## Dependency Freeze
PASS / FAIL

## Config Freeze
PASS / FAIL

## Secret Audit
PASS / FAIL

## Terraform / azd
PASS / FAIL

## Clean Build Pass 1
PASS / FAIL

## Preflight
PASS / FAIL

## Phase 1 Critical Regression
PASS / FAIL

## Phase 2 Core Regression
PASS / FAIL

## Phase 3 Evidence Integrity
PASS / FAIL

## Phase 4 Production Regression
PASS / FAIL

## Signature Demo
PASS / FAIL

## Recovery
PASS / FAIL

## Evidence Package
PASS / FAIL

## Adaptation Boundary
PASS / FAIL

## Clean Build Pass 2
PASS / FAIL

## Full Chain Pass 1
PASS / FAIL

## Full Chain Pass 2
PASS / FAIL

## Release Tag
...

## Known Limitations
...

## Architecture Change Required?
YES / NO

## Phase 5 Result
PASS / BLOCKED
```

---

# 35. Phase 5 PASS Gate

Return:

```text
PHASE 5 RESULT: PASS
```

only when all mandatory conditions are true:

```text
[ ] Phase 4 prerequisite PASS

[ ] dependencies pinned

[ ] frozen manifest matches deployment

[ ] no exposed secret

[ ] Terraform validates

[ ] azure.yaml matches frozen design

[ ] clean build PASS twice

[ ] preflight PASS

[ ] Phase 1 critical regression PASS

[ ] Phase 2 core regression PASS

[ ] Phase 3 evidence recomputes correctly

[ ] full benchmark rerun performed if core behavior changed

[ ] microbenchmark remains attributable to current core

[ ] Phase 4 production regression PASS

[ ] Judge Mode uses real data

[ ] all four signature demos PASS three consecutive times

[ ] rollback PASS

[ ] Stable recovery PASS

[ ] recovery tooling PASS

[ ] backup evidence package complete

[ ] competition adaptation boundary documented

[ ] gap-analysis template ready

[ ] known limitations documented

[ ] full clean-start chain PASS twice

[ ] no architecture assumption failed

[ ] final release manifest is internally consistent
```

---

# 36. BLOCKED Gate

Return:

```text
PHASE 5 RESULT: BLOCKED
```

if any competition-critical condition fails.

Examples:

```text
second clean build fails
hidden dependency drift
benchmark no longer matches current core
demo requires manual repair
APIM rollback unreliable
Judge Mode depends on hard-coded data
secret leaked into evidence
recovery path cannot restore frozen state
```

---

# 37. Final Release Decision

If PASS:

```text
Architecture = FROZEN
Implementation = VALIDATED
Evidence = PRESERVED
Recovery = READY
Competition RC = READY
```

Allowed work after this point:

```text
bug fixes
copy editing
visual polish
video editing
submission packaging
official-brief adaptation
```

Not allowed by default:

```text
architecture redesign
new reliability mechanism
new state ownership model
new infrastructure dependency
new agent framework
```

---

# 38. Final Validator Instruction

The goal of Phase 5 is not to make ReasonFuse more sophisticated.

The goal is to make it hard to break.

A successful final state looks like:

```text
one frozen release
one reproducible build
one verified benchmark
one known deployment path
one known rollback path
one known recovery path
four repeatable demos
two clean full-chain passes
```

At that point, the project is ready for the official competition brief.
