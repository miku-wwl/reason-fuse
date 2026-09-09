# ReasonFuse Phase 5 — Pre-Competition Freeze Construction Prompt

> **Purpose:** Freeze, harden, package, and make ReasonFuse reproducible before the competition brief is published.  
> **Audience:** GPT-6 Astra / coding agent  
> **Phase:** 5 — Pre-Competition Freeze  
> **Expected effort:** 4–6 hours  
> **Prerequisite:** Phase 4 Production Story = **PASS**  
> **Architecture status:** FROZEN  
> **Feature policy:** NO NEW FEATURES  
> **Primary Exit Gate:** `clean-start full-chain PASS + dependencies pinned + rollback/demo/benchmark evidence preserved + recovery package ready`

---

# 1. Mission

Phase 5 is not a development phase.

It is the final hardening and freeze phase before the competition brief is published.

Your job is to convert the working ReasonFuse system into a reproducible, recoverable, competition-ready release.

The Phase 5 objective is:

```text
Freeze
↓
Rebuild from clean state
↓
Run complete regression
↓
Preserve evidence
↓
Create recovery paths
↓
Lock the system
```

Do not improve architecture.

Do not add features.

Do not introduce optional Preview dependencies.

Do not refactor for elegance unless a verified bug requires it.

---

# 2. Hard Prerequisite

Before making changes, inspect:

```text
PHASE4_REPORT.md
```

Required:

```text
PHASE 4 RESULT: PASS
```

At minimum:

```text
Stable/Candidate PASS
APIM weighted canary PASS
session affinity PASS
SSE PASS
Tracing PASS
Judge Mode PASS
OFF/ON PASS
Unknown Correct Path PASS
Outcome Failure PASS
Candidate Regression PASS
Rollback PASS
Clean-start E2E PASS
```

If Phase 4 is not PASS:

```text
STOP
```

Do not freeze a partially validated system.

---

# 3. Phase 5 Golden Rule

From this point onward:

```text
NO NEW ARCHITECTURE
NO NEW PRODUCT FEATURES
NO NEW BENCHMARK CATEGORIES
NO NEW DETECTORS
NO NEW AZURE SERVICES
NO FRAMEWORK UPGRADES
```

Allowed changes:

```text
bug fix
test stabilization
dependency pinning
script repair
documentation correction
evidence packaging
recovery tooling
small UI wording fix
demo reliability fix
```

Any change that affects system behavior must trigger regression reruns.

---

# 4. Freeze Target

Create a named release candidate.

Recommended:

```text
ReasonFuse Competition RC1
```

Record:

```text
git commit
git tag
agent_version
stable_agent_version
candidate_agent_version
model_version
prompt_version
toolbox_version
knowledge_base_version
reasonfuse_contract_version
dataset_version

agent_framework_version
foundry_hosting_version
azure_ai_projects_version

terraform_version
azurerm_provider_version
azapi_provider_version

azd_version
python_version
```

---

# 5. Dependency Freeze

Verify exact pins.

Required:

```text
pyproject.toml
uv.lock
requirements.txt
```

`requirements.txt` must contain exact versions for remote build.

Do not leave floating constraints such as:

```text
>=
~
latest
*
```

for competition-critical dependencies unless technically unavoidable.

If unavoidable, document the reason.

---

# 6. Competition-Window Upgrade Policy

Create a written freeze rule:

```text
Do not upgrade:
- Agent Framework
- Foundry hosting packages
- azure-ai-projects
- Azure SDK dependencies
- Terraform providers
- model deployment
- Toolbox version
- knowledge base version

during the competition window unless:
a blocking defect exists
AND
the change is validated
AND
full regression is rerun
```

Store this policy in the repository.

---

# 7. Configuration Freeze

Create one machine-readable release manifest.

Recommended:

```text
release/competition_rc1.yaml
```

Include:

```text
release_name
git_commit

stable_agent_version
candidate_agent_version

model_version
prompt_version
toolbox_version
knowledge_base_version
reasonfuse_contract_version
dataset_version

dependencies
terraform_versions

APIM:
  stable_weight
  candidate_weight
  session_affinity

benchmark:
  scenario_count
  repetitions
  expected_valid_runs
```

This manifest becomes the source of truth for the frozen competition build.

---

# 8. Secret / Environment Audit

Verify no secret is committed.

Search for:

```text
API keys
tokens
passwords
connection strings
subscription secrets
private certificates
authorization headers
```

Confirm secret handling uses:

```text
environment variables
managed identity
Key Vault if already present
local secret files excluded by git
```

Do not introduce Key Vault merely for Phase 5 if it is not required by the existing design.

---

# 9. Terraform Freeze

Run:

```text
terraform fmt
terraform validate
terraform plan
```

Capture evidence.

The frozen Terraform should recreate required supporting infrastructure.

Avoid unnecessary drift.

Record any intentionally external/data-plane resource managed through:

```text
azd
azure.yaml
Foundry deployment
```

Do not force everything into Terraform.

---

# 10. `azure.yaml` Freeze

Validate:

```text
Responses 2.0.0
Hosted Agent deployment settings
remote_build
runtime version
entry point
```

Confirm no accidental config drift between documentation and actual deployment.

---

# 11. Clean-Start Build Script

Create or harden:

```text
scripts/clean_build.sh
```

or equivalent.

It should execute a documented sequence:

```text
validate environment
↓
install exact dependencies
↓
terraform init
↓
terraform validate
↓
terraform apply / verify infra
↓
azd provision if required
↓
azd deploy
↓
verify agent endpoints
↓
verify Toolbox
↓
run preflight
```

Do not require manual code edits during this sequence.

---

# 12. Preflight Script

Create or harden:

```text
demo/preflight.sh
```

It must verify at minimum:

```text
authentication
RBAC
Hosted Agent Stable reachable
Hosted Agent Candidate reachable
Responses endpoint
Toolbox reachable
tools/list
Operations API
AgentSession behavior smoke
Function Middleware interception smoke
R2 approval smoke
APIM endpoint
APIM affinity
SSE
Foundry tracing
Application Insights ingestion
Judge Mode backend
```

Fail non-zero on required check failure.

---

# 13. Reset Script

Create or harden:

```text
demo/reset.sh
```

It must reset:

```text
scenario world state
tool execution counters
approval state
fault configuration
AgentSession test state
conversation/session IDs as appropriate
demo artifacts
candidate rollback state
```

A demo must not depend on hidden state from the previous run.

---

# 14. Full Regression Suite

Create one top-level script:

```text
scripts/run_full_regression.sh
```

Required sequence:

```text
Phase 1 critical runtime smoke
↓
Phase 2 ReasonFuse core regression
↓
Phase 3 benchmark integrity smoke
↓
Phase 4 production-story regression
↓
final clean-start signature demo
```

Do not rerun every historical exploratory test if not useful.

But competition-critical invariants must be included.

---

# 15. Phase 1 Critical Regression

Revalidate:

```text
Responses history ownership
AgentSession persistence
Toolbox BEFORE/AFTER interception
Toolbox BLOCK before execution
R2 approval round-trip
APIM affinity
SSE
```

These are architecture-critical assumptions.

---

# 16. Phase 2 Core Regression

Revalidate:

```text
OFF baseline
ON no-progress containment
Exact Loop
Oscillation
Retrieval Churn
Useful Recheck
Todo-only change does not count as objective progress
Run Contract
Outcome Verified
Postcondition Failed
```

---

# 17. Phase 3 Evidence Regression

Do not necessarily rerun the entire 300-run benchmark unless a core behavior changed.

At minimum:

```text
verify frozen 300-run raw evidence exists
verify report recomputes
verify confusion matrix recomputes
verify metrics recompute
verify 10,000-event microbenchmark artifact exists
```

If Phase 5 changes detector logic or Run Contract behavior:

```text
rerun the full 300-run benchmark
```

No exceptions.

---

# 18. Phase 4 Production Regression

Revalidate:

```text
Stable/Candidate version matrix
APIM 95/5
session affinity
SSE
release lineage
Foundry tracing
Judge Mode
Candidate Regression
rollback
Stable recovery after rollback
```

---

# 19. Signature Demo Regression

Run the four signature scenarios:

```text
A — OFF / ON
B — Unknown Correct Path
C — Outcome Failure
D — Candidate Regression
```

Each must run cleanly.

At minimum:

```text
3 consecutive PASS runs
```

after reset.

---

# 20. Judge Mode Freeze

Freeze Judge Mode semantics.

Required message:

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
Fuse Reason
Containment Latency
Release Role
```

Primary line:

```text
Planning changed. Reality did not.
```

Secondary system message:

```text
Execution success is not outcome success.
```

Do not perform a visual redesign in Phase 5 unless clarity is broken.

---

# 21. Benchmark Evidence Package

Create a competition evidence package.

Recommended:

```text
evidence/frozen/
├── phase1/
├── phase2/
├── phase3/
├── phase4/
├── benchmark/
│   ├── raw/
│   ├── normalized/
│   ├── confusion_matrix.*
│   ├── metrics.*
│   └── microbenchmark.*
│
├── traces/
├── screenshots/
└── release_manifest/
```

Do not overwrite original raw evidence.

---

# 22. Screenshot / Trace Capture

Capture stable evidence for:

```text
Foundry Hosted Agent
Toolbox
Foundry IQ / retrieval path if shown
Foundry Tracing
Application Insights
Judge Mode
APIM backend pool
APIM affinity proof
SSE proof
Outcome Failure
Candidate Regression
Rollback
benchmark summary
confusion matrix
```

These are backup proof in case the live demo environment becomes unreliable.

---

# 23. Backup Demo Assets

Create backup artifacts for each signature scenario:

```text
Judge Mode screenshot
trace screenshot
raw output
expected tool sequence
final result
```

Optional:

```text
short screen recording
```

if easy to capture.

The purpose is recovery, not final video production.

---

# 24. Rollback Safety

Before freeze:

```text
restore intended production/demo APIM weights
```

Recommended default:

```text
Stable = 95
Candidate = 5
```

or:

```text
Stable = 100
Candidate = 0
```

if you intentionally want a safer frozen resting state.

Document the chosen freeze state.

Also document one command to restore the demo canary.

---

# 25. One-Command Demo Preparation

Create:

```text
demo/prepare_demo.sh
```

It should:

```text
preflight
reset
restore expected APIM demo state
verify Stable/Candidate
verify scenario API
verify Judge Mode
print READY
```

Target final output:

```text
REASONFUSE DEMO READY
```

---

# 26. One-Command Emergency Recovery

Create:

```text
scripts/emergency_recover.sh
```

Its scope should be narrow and safe.

It may:

```text
restore known APIM weights
restart/redeploy known agent version
restore frozen config
rerun preflight
```

Do not create destructive recovery logic.

Do not destroy infrastructure by default.

---

# 27. Recovery Documentation

Create:

```text
RECOVERY_RUNBOOK.md
```

Include:

```text
Agent endpoint down
Toolbox unavailable
APIM routing wrong
Affinity lost
SSE buffered
Judge Mode unavailable
Application Insights delayed
Candidate still receiving traffic
Operations API dirty state
Deployment drift
```

For each:

```text
symptom
check
safe recovery action
verification
```

---

# 28. Competition-Day Change Boundary

Create:

```text
COMPETITION_ADAPTATION_BOUNDARY.md
```

Allowed after 9/17 brief release:

```text
prompt changes
scenario wording
runbook content
tool descriptions
Judge Mode copy
demo story
benchmark subset
README/pitch
business-domain mapping
```

Not allowed without strong cause:

```text
ReasonFuse core rewrite
new architecture
new database
new agent runtime
new release platform
new major detector
new state ownership model
new approval model
```

---

# 29. 9/17 Gap-Analysis Template

Create:

```text
COMPETITION_GAP_ANALYSIS_TEMPLATE.md
```

Template:

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

This will be used after the brief is published.

---

# 30. Freeze Changelog

Create a concise changelog for the RC.

Example:

```text
ReasonFuse Competition RC1

Architecture:
UNCHANGED

Core:
UNCHANGED except verified bug fixes

Dependencies:
PINNED

Benchmark:
FROZEN

Judge Mode:
FROZEN

APIM:
FROZEN

Known limitations:
...
```

---

# 31. Known-Limitations Register

Create:

```text
KNOWN_LIMITATIONS.md
```

Only list real, observed limitations.

Examples:

```text
Preview evaluator unavailable
App Insights ingestion may lag
active Candidate sessions may persist after rollback
specific SDK workaround required
```

Do not hide known issues.

Do not speculate excessively.

---

# 32. Final Repository Hygiene

Check:

```text
no dead experimental code on main path
no temporary debug secrets
no giant generated files accidentally committed
no stale alternate architecture docs presented as current
no duplicate config source of truth
```

Keep historical evidence if useful, but make current frozen release obvious.

---

# 33. Release Tag

Create a release tag only after validation succeeds.

Recommended:

```text
reasonfuse-competition-rc1
```

Do not tag before independent Phase 5 verification.

Construction should prepare for the tag, not self-certify it.

---

# 34. Phase 5 Construction Report

Create:

```text
PHASE5_REPORT.md
```

Template:

```text
# Phase 5 Pre-Competition Freeze Report

## Release Candidate
Name:
Git commit:
Proposed tag:

## Architecture
UNCHANGED / CHANGED

## Dependency Freeze
Status:

## Terraform Freeze
Status:

## azure.yaml Freeze
Status:

## Preflight
Status:

## Full Regression
Status:

## Signature Demo
Status:

## Benchmark Evidence Preservation
Status:

## Judge Mode Freeze
Status:

## Recovery Scripts
Status:

## Recovery Runbook
Status:

## Competition Adaptation Boundary
Status:

## Known Limitations
...

## Architecture Change Required?
YES / NO

## Phase 5 Result
NOT VALIDATED / PASS / BLOCKED
```

---

# 35. What Phase 5 Must NOT Do

Do not:

```text
add P0.5 features
add AI Red Teaming
add automatic rollback if not already present
add new natural incidents
increase benchmark scope
redesign UI
rewrite ReasonFuse
upgrade SDKs for novelty
change model for curiosity
change Toolbox version casually
change knowledge base casually
```

The system is being frozen, not expanded.

---

# 36. Construction Completion Criteria

Construction is complete when:

```text
[ ] release manifest exists

[ ] dependencies exactly pinned

[ ] competition upgrade policy documented

[ ] Terraform validates

[ ] azure.yaml frozen

[ ] secret audit completed

[ ] clean build script exists

[ ] preflight script hardened

[ ] reset script hardened

[ ] full regression script exists

[ ] signature demo script exists

[ ] demo preparation script exists

[ ] emergency recovery script exists

[ ] recovery runbook exists

[ ] competition adaptation boundary exists

[ ] gap-analysis template exists

[ ] known-limitations register exists

[ ] evidence package structure exists

[ ] benchmark raw evidence preserved

[ ] Phase 5 report template exists
```

At construction completion, state:

```text
PHASE 5 CONSTRUCTION COMPLETE
READY FOR INDEPENDENT VALIDATION
```

Do not self-award Phase 5 PASS.
