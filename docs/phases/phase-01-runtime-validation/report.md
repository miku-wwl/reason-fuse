# Phase 1 Runtime Validation Report

> This is the construction-run report. Source files now live at the repository root;
> original run evidence is archived without byte changes. See the
> [repository reorganization record](reorganization.md) for subsequent layout checks.

Construction status: **PHASE 1 CONSTRUCTION COMPLETE / READY FOR INDEPENDENT VALIDATION**.
The separate Phase 1 acceptance status is stated at the end of this report.

## Environment

- Integration runs: 2026-09-07 UTC; construction closeout: 2026-09-08 (Pacific/Auckland).
- Subscription: Azure for Students, `7c73b89d-485e-43a9-8d66-b12b766d567f`
- Resource group: `rg-reasonfuse-phase1-aue`
- Foundry account / project: `cog-cce5b59dd73ad` / `reasonfuse-phase1`
- Region: Australia East (`australiaeast`), enforced by Terraform variable validation.
- Model: `gpt-5-mini`, version `2025-08-07`, GlobalStandard capacity 10.
- Python: local interpreter 3.13.9; hosted interpreter 3.13.15, observed through the state tool.
- Agent Framework: `agent-framework-core==1.17.0`. The `agent-framework` umbrella
  package is intentionally omitted because it installs all optional integrations.
  The normal `agent_framework.Agent`, TodoProvider and AgentModeProvider come from core.
- `agent-framework-foundry==1.12.0`
- `agent-framework-foundry-hosting==1.0.0b260903`
- `azure-ai-projects==2.3.0` (Foundry integration requires `<2.4.0`)
- `azure-identity==1.25.3`
- `azure-ai-agentserver-responses==2.2.0b1`
- All transitive dependencies: exact versions in `uv.lock` and `requirements.txt`;
  106 pinned distributions, verified against the frozen uv export. uv: 0.11.16.
- azd: 1.33.0, project-local executable; agent extension 1.0.0-beta.13,
  project extension 1.0.0-beta.9, toolbox extension 1.0.0-beta.6.
- Terraform: 1.14.0; AzureRM: 5.4.0; AzAPI: 2.12.0.
- APIM: Consumption; Operations API: single-process Python on Linux App Service F1.
- Monitoring: Application Insights and Log Analytics in Australia East.
- Deployed agents: stable version 4 and candidate version 1, both Responses 2.0.0.
- Toolbox: `reasonfuse-operations`, version 2 (DNS and approval-gated restart).
- Resource inventory: [resource-inventory.json](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/resource-inventory.json). All regional resources
  are in Australia East; Azure's Application Insights Smart Detection action group
  is a global resource.

## Spike 1

Status: PASS

Real Hosted Agent version 4, Responses 2.0.0, `history_source="agent_server"`,
downstream `store=False`. Two turns returned INC-001 and the same framework session
ID. State RF-STATE-001 and counter 7 survived; turn number advanced 1 to 2;
restored_at_turn_start changed false to true. Input message counts were 1 and 9.
No application transcript or session store was introduced. The SDK adds its own
non-loading hosted-history sentinel provider; this is not a second transcript store.

Evidence:

- [20260907T090340042860Z-spike01_history_session.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T090340042860Z-spike01_history_session.jsonl) (final version 4)
- [20260907T035943692688Z-spike01_history_session.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T035943692688Z-spike01_history_session.jsonl)
- [stable-deployment.json](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/stable-deployment.json)
- [provision-baseline.log](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/provision-baseline.log)
- [deploy-stable.log](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/deploy-stable.log)

Limits: cold-start restoration and arbitrary concurrent/forked turns were not tested.

## Spike 2

Status: PASS

Real Toolbox version 1 initially exposes only DNS. Real tools/list returns
`operations___dns_resolution`, with an OpenAPI request-body wrapper. The runtime
whitelist uses that observed name. Function middleware records BEFORE/AFTER and
blocks the specified hostname before dispatch. External counters use an epoch;
a changed epoch invalidates the non-execution assertion.

Evidence:

- [20260907T090443066967Z-spike02_toolbox_allow.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T090443066967Z-spike02_toolbox_allow.jsonl) (final version 4)
- [20260907T090540144147Z-spike02_toolbox_block.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T090540144147Z-spike02_toolbox_block.jsonl) (final version 4)
- [20260907T084910663096Z-spike02_toolbox_allow.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T084910663096Z-spike02_toolbox_allow.jsonl)
- [20260907T085015482091Z-spike02_toolbox_block.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T085015482091Z-spike02_toolbox_block.jsonl)
- [20260907T041008198739Z-toolbox-provision.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T041008198739Z-toolbox-provision.jsonl)
- [20260907T041216785589Z-toolbox-smoke.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T041216785589Z-toolbox-smoke.jsonl)

Hosted version 3 captured BEFORE/AFTER with the real returned INCONCLUSIVE result;
external execution count was 1. Blocked hostname produced BEFORE/BLOCK and external
count 0, under an unchanged counter epoch. The first allow run failed because the
evidence serializer captured Content object addresses rather than text. The
serializer was repaired and both real cases rerun; no architecture substitution.
Both cases were also rerun successfully on final version 4 with Toolbox version 2.
The earlier failed evidence remains at
[20260907T084505966906Z-spike02_toolbox_allow.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T084505966906Z-spike02_toolbox_allow.jsonl).

## Spike 3

Status: PASS

Native Agent Framework approval and Foundry hosting approval storage are used.
The R2 runtime rule is `always_require` for the exact discovered restart
tool name. No custom approval database or alternative resume path is implemented.

Stable version 4 and Toolbox version 2 completed all three real cases. Each action
paused with an `mcp_approval_request` before external execution. Approval of the
exact `orders` arguments produced one external execution; denial produced zero.
Reusing the consumed approval while requesting `payments` did not execute another
action; a distinct approval was required and denied. Counter 7 and the framework
session ID survived each approval/denial round-trip. Counter epochs were unchanged.

Evidence:

- [20260907T085519120528Z-spike03_approval_approve.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T085519120528Z-spike03_approval_approve.jsonl)
- [20260907T085637748628Z-spike03_approval_deny.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T085637748628Z-spike03_approval_deny.jsonl)
- [20260907T085757647760Z-spike03_approval_binding.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T085757647760Z-spike03_approval_binding.jsonl)
- [20260907T085157844740Z-toolbox-smoke.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T085157844740Z-toolbox-smoke.jsonl)
- [environment-current.json](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/environment-current.json)

## Spike 4

Status: PASS

Native APIM pool is configured for stable 95 / candidate 5 and the
ReasonFuseAffinity cookie, using AzAPI backend API 2025-03-01-preview.
Policy uses `buffer-response=false`; no caching or body-inspection policies.
All four frontend/backend request/response diagnostic body byte limits are 0.
Deterministic probe middleware yields four real chunks separated by 750 ms.

Evidence:

- [provision-supporting.log](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/provision-supporting.log)
- [20260907T091424968527Z-preflight.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T091424968527Z-preflight.jsonl): actual ARM readback confirms
  stable weight 95, candidate weight 5, native cookie affinity, streaming policy,
  metadata sampling 100%, empty captured-header lists and four body limits of 0.
- [20260907T090042566001Z-spike04_affinity.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T090042566001Z-spike04_affinity.jsonl): 8 turns shared one
  framework-hosted platform session and the stable backend, using the native cookie.
- [20260907T090214407062Z-spike04_sse.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T090214407062Z-spike04_sse.jsonl): four actual text delta
  arrivals at 16.229, 16.985, 17.732 and 18.488 seconds after request start;
  adjacent gaps were about 0.75 seconds, with `response.completed` observed.
- [20260907T090547133100Z-metadata_telemetry.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T090547133100Z-metadata_telemetry.jsonl): 20 real APIM
  request metadata rows queried from Log Analytics, including status, duration and
  operation IDs. The query excludes bodies and authorization headers.
- [20260907T090247677322Z-spike04_new_session_control.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T090247677322Z-spike04_new_session_control.jsonl): 60 fresh
  HTTP clients observed stable 58 and candidate 2. Both backends were reached.
  Candidate fraction was 3.33%; the 99% Wilson interval was 0.65%-15.31%, containing
  the configured 5%. This establishes the fresh-cookie routing control and is
  not a precise estimate of the configured ratio.

The release and SSE probes use deterministic Agent middleware, bypassing model inference while exercising the
real Hosted Agent and APIM transport. Time to first chunk includes cold-start and
transport overhead; this experiment is not a latency benchmark.

## Construction verification and handoff

All nine requested real integration cases have PASS results with exit code 0.
These are construction-time checks; an independent validation procedure has not
been executed. Individual spike PASS labels refer only to the evidence above.

The complete preflight entry point passed ([preflight-complete.log](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/preflight-complete.log)):
doctor reported 11 passed, 0 failed and 2 skipped. Its Toolbox/connection discovery
checks were skipped because these assets are SDK-created, not declared as azd
services. The separate real Toolbox smoke covered tools/list, DNS execution and
local approval modes ([20260907T091332558184Z-toolbox-smoke.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T091332558184Z-toolbox-smoke.jsonl)).
Direct stable, candidate and APIM probes also passed.

Earlier failed diagnostic attempts are retained. The telemetry query initially
hit AzureCliCredential's 10-second process timeout; a 60-second timeout resolved
it. Two policy-readback attempts failed because of Windows CLI BOM handling and
XML/JSON content negotiation. Explicit JSON negotiation and BOM-tolerant parsing
resolved the validator issue; no APIM deployment or frozen architecture was changed.

Reset passed at 2026-09-07 13:00 UTC (2026-09-08 01:00 Pacific/Auckland).
Across the initial and corrected runs, deletion requests covered all 84 recorded
native test sessions (77 stable and 7 candidate). Final native readback contained
no non-deleted recorded sessions, both external counter snapshots were empty under
the same epoch, and the local reset fixture was removed. Evidence was retained.

The initial reset incorrectly required deleted rows to disappear from the session
listing. Foundry can return their metadata with `status=deleted`; the pinned SDK
explicitly models this terminal status. The reset validator now accepts absence
or explicit `deleted` and rejects every other status. The first failure, read-only
investigation and successful rerun are all retained:

- [20260907T125621735996Z-reset.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T125621735996Z-reset.jsonl)
- [20260907T125853379600Z-reset-investigation.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T125853379600Z-reset-investigation.jsonl)
- [20260907T130009682767Z-reset.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T130009682767Z-reset.jsonl)
- [reset-complete.log](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/reset-complete.log)

Final artifact checks passed: Python/PowerShell syntax, TOML/YAML parsing, exact
requirements/export agreement and a known-secret-value scan of shareable files.
Terraform validation had already passed on the deployed configuration. The final
read-only deployment snapshot still reports stable 4 and candidate 1 as active,
with the same deployed content hash and Responses 2.0.0:
[20260907T125818818409Z-environment.jsonl](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/20260907T125818818409Z-environment.jsonl).
The evidence index is [construction-handoff.json](../../../evidence/phase-01-runtime-validation/construction-2026-09-07/construction-handoff.json).

Construction exit checklist:

- [x] Minimal Foundry Hosted Agent deploys.
- [x] Responses 2.0.0 configured.
- [x] `history_source="agent_server"` configured.
- [x] Downstream `store=False` configured.
- [x] AgentSession test state implemented.
- [x] TodoProvider / AgentModeProvider minimally composed.
- [x] Toolbox tool is real and callable.
- [x] Function Middleware can inspect calls.
- [x] Block mechanism is implemented and exercised.
- [x] R2 approval flow is implemented.
- [x] Approve and deny paths exist and execute through the native protocol.
- [x] Independent execution counters exist.
- [x] Stable/Candidate backends exist.
- [x] APIM weighted pool configured.
- [x] Session affinity configured and exercised.
- [x] SSE configuration applied and four timed chunks observed.
- [x] Reset/deploy/preflight scripts exist; reset and full preflight passed.
- [x] All nine validation scripts/cases ran successfully.
- [x] Evidence directory contains real integration results.
- [x] This report records outcomes, failures, versions and limits.

Limits: separate independent acceptance, a clean destroy/redeploy, production
hardening, real service restarts, forced cold-start state recovery and arbitrary
concurrent/forked turns are NOT VERIFIED. The restart API intentionally simulates
the action and records its execution count. Azure resources are retained for the
independent validation run.

## Architecture Unfreeze Required?

NO - all four bounded integration spikes passed without changing the frozen architecture.

## Phase 1 Result

NOT COMPLETE

**PHASE 1 CONSTRUCTION COMPLETE**

**READY FOR INDEPENDENT VALIDATION**

Phase 1 remains NOT COMPLETE pending the separate independent validation
procedure. Construction-time integration checks are complete; this report does
not claim independent Phase 1 acceptance.
