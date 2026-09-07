# ReasonFuse Phase 1 — Runtime Validation Construction Prompt

> **Purpose:** Build the minimum implementation needed to validate the frozen ReasonFuse v4.1.3 architecture.  
> **Audience:** GPT-6 Astra / coding agent  
> **Phase:** 1 — Runtime Validation  
> **Expected effort:** 6–8 hours  
> **Architecture status:** FROZEN  
> **Important:** This phase is NOT the ReasonFuse product implementation phase.

---

# 1. Mission

You are implementing only the minimum runtime-validation scaffolding required to test four architecture-critical assumptions.

Do **not** build the full ReasonFuse product.

Do **not** add services, databases, frameworks, persistence layers, queues, orchestration platforms, or abstractions that are not necessary for these four validation spikes.

The four spikes are:

```text
Spike 1 — Responses History + AgentSession

Spike 2 — Local Toolbox Interception

Spike 3 — R2 Human Approval Round-trip

Spike 4 — APIM Sticky Canary + SSE
```

The frozen architecture is:

```text
User
 ↓
Azure API Management
 ↓
Foundry Hosted Agent
 ↓
Responses Protocol 2.0.0
 ↓
ResponsesHostServer(
    history_source="agent_server"
)
 ↓
Microsoft Agent Framework Agent
 ├─ TodoProvider
 ├─ AgentModeProvider
 ├─ AgentSession
 ├─ Tool Approval
 └─ ReasonFuse Middleware
      ↓
Local Tool / MCP Invocation
      ↓
Foundry Toolbox
 ├─ Foundry IQ
 └─ Operations OpenAPI
```

For Phase 1, implement only enough of this architecture to validate its critical runtime assumptions.

---

# 2. Non-Negotiable Rules

## Rule 1 — Do Not Redesign the Architecture

If a frozen assumption fails:

```text
STOP
preserve evidence
explain the failure
mark the spike FAIL
```

Do not silently replace it with another architecture.

Do not add:

```text
Redis
Cosmos DB
Postgres
AKS
Kubernetes
Durable Functions
Service Bus
Event Hub
custom MCP transport
custom conversation store
custom approval database
custom session manager
multi-agent orchestration
```

unless Phase 1 explicitly requires it, which currently it does not.

---

## Rule 2 — Code Completion Is Not Success

A spike is not complete because:

```text
code compiles
tests are written
Terraform plans
Microsoft documentation says it should work
a mock passes
```

A spike passes only after the real execution path runs and evidence is captured.

---

## Rule 3 — Keep the Implementation Small

Prefer:

```text
one minimal Hosted Agent
one minimal Toolbox
one deterministic Operations API
one tiny middleware
one minimal APIM configuration
```

over production-scale abstractions.

---

## Rule 4 — Preserve Reproducibility

Use exact dependency versions.

Create:

```text
pyproject.toml
uv.lock
requirements.txt
```

`requirements.txt` must use exact versions suitable for Foundry remote build.

Record versions in the Phase 1 report:

```text
agent-framework
agent-framework-foundry
agent-framework-foundry-hosting
azure-ai-projects
azure-identity
azd
terraform
azurerm provider
azapi provider if used
```

---

# 3. Phase 1 Repository Layout

Create a structure similar to:

```text
phase1-runtime-validation/
│
├── azure.yaml
├── pyproject.toml
├── requirements.txt
├── uv.lock
│
├── src/
│   ├── main.py
│   ├── agent.py
│   ├── session_state.py
│   └── middleware/
│       └── validation_middleware.py
│
├── operations-api/
│   ├── openapi.yaml
│   ├── dns_resolution.py
│   └── restart_service.py
│
├── toolbox/
│   └── operations-toolbox.yaml
│
├── infra/
│   ├── providers.tf
│   ├── main.tf
│   ├── identity.tf
│   ├── apim.tf
│   ├── monitoring.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── spikes/
│   ├── spike01_history_session/
│   ├── spike02_toolbox_interception/
│   ├── spike03_approval/
│   └── spike04_apim/
│
├── evidence/
│
├── scripts/
│   ├── deploy.sh
│   ├── reset.sh
│   └── preflight.sh
│
└── PHASE1_REPORT.md
```

You may simplify this if a smaller structure is sufficient.

Do not create abstraction layers that are not required.

---

# 4. Infrastructure Scope

Use Terraform for supporting Azure infrastructure where practical.

Use:

```text
azure.yaml / azd
```

for Foundry Hosted Agent deployment and Foundry-managed data-plane assets where appropriate.

Terraform Phase 1 scope should be limited to what the spikes need:

```text
Resource Group if needed
RBAC
Application Insights / monitoring support
Azure API Management
supporting resources required by the Hosted Agent
```

Do not spend Phase 1 implementing:

```text
private networking
multi-region
HA
advanced dashboards
enterprise policy
production networking hardening
complex cost governance
```

If AzureRM does not expose an APIM feature required by the spike, use AzAPI rather than redesigning the release architecture.

---

# 5. Hosted Agent Baseline

Create the smallest valid Hosted Agent using:

```text
Responses Protocol 2.0.0
```

Host configuration:

```text
ResponsesHostServer(
    history_source="agent_server"
)
```

The downstream Agent/model client should avoid storing a second canonical history:

```text
default_options = {
    "store": False
}
```

Use a normal Agent Framework Agent.

Compose only what Phase 1 needs:

```text
AgentSession
TodoProvider
AgentModeProvider
Tool Approval
validation middleware
```

Do not use the Full Harness bundle.

---

# 6. Spike 1 Construction — Responses History + AgentSession

## Goal

Build the minimum path required to verify:

```text
Foundry Agent Server
= canonical conversation-history owner

AgentSession
= runtime/provider/ReasonFuse state owner
```

## Implementation

The agent must support a multi-turn conversation.

Add minimal test state:

```text
reasonfuse_test_state = "RF-STATE-001"
```

Store this in AgentSession state.

Test conversation:

```text
Turn 1:
"My service is unhealthy. Remember incident ID INC-001."

Turn 2:
"What incident ID are we investigating?"
```

Expected answer:

```text
INC-001
```

Also verify:

```text
AgentSession state still contains RF-STATE-001
```

Do not add a second canonical transcript store.

## Required Logging

Capture:

```text
conversation_id
agent_session_id
turn number
reasonfuse_test_state
message counts if observable
```

## Construction Exit

Code for Spike 1 is complete only when the real Hosted Agent path is ready for validation.

---

# 7. Spike 2 Construction — Local Toolbox Interception

## Goal

Build the minimum path required to prove:

```text
Agent Framework
 ↓
Function Calling Middleware
 ↓
Local Toolbox invocation
 ↓
Foundry Toolbox
```

is interceptable before and after tool execution.

## Toolbox

Expose exactly one simple tool initially:

```text
dns_resolution(hostname)
```

Deterministic result:

```json
{
  "hostname": "api.reasonfuse.local",
  "status": "INCONCLUSIVE"
}
```

Use:

```text
FoundryToolbox
```

if compatible with the pinned package versions.

Fallback:

```text
MCPStreamableHTTPTool
```

Do not implement a custom MCP transport.

## Temporary Validation Middleware

Implement logic equivalent to:

```text
BEFORE <tool_name> <args>

await next()

AFTER <tool_name> <result>
```

Also implement a block rule:

```text
if hostname == "blocked.reasonfuse.local":
    BLOCK BEFORE EXECUTION
```

The blocked path must not call the external tool.

## Required Instrumentation

The tool implementation must increment or record an execution counter so that a blocked request can prove:

```text
tool execution count = 0
```

Do not rely only on middleware logs.

---

# 8. Spike 3 Construction — R2 Human Approval

## Goal

Build the minimum approval round-trip.

Create:

```text
restart_service(service_name)
```

Risk:

```text
R2 — HIGH_IMPACT_WRITE
```

Configure:

```text
always require approval
```

The function should have a deterministic external execution counter.

Before the approval request, put:

```text
reasonfuse_test_counter = 7
```

in AgentSession.

Required behavior:

```text
tool request
→ pause
→ approval required
→ approve exact action
→ resume
→ execute once
```

Also support denial:

```text
deny
→ tool execution count remains 0
```

Approval must not be reusable for a different argument set.

Example:

```text
approve:
restart_service("orders")

must NOT authorize:
restart_service("payments")
```

---

# 9. Spike 4 Construction — APIM Sticky Canary + SSE

## Goal

Build the minimum APIM setup required to validate:

```text
weighted routing
session affinity
SSE pass-through
```

Create two minimal Hosted Agent backends:

```text
Stable
→ release_role = "stable"

Candidate
→ release_role = "candidate"
```

APIM target:

```text
Stable weight    = 95
Candidate weight = 5
session affinity = ON
```

The client must preserve APIM affinity state across turns.

Implement a test client that uses one persistent HTTP session.

## Streaming

Configure:

```text
buffer-response = false
response caching = OFF
streaming body diagnostics = OFF
metadata telemetry = ON
```

Create a streaming response that emits multiple observable chunks.

Example:

```text
chunk-1
chunk-2
chunk-3
chunk-4
```

Do not fake streaming by returning one complete response.

---

# 10. Scripts

Create the following minimal scripts.

## `scripts/deploy.sh`

Should:

```text
validate dependencies
terraform init/plan/apply as needed
azd provision/deploy as needed
print important endpoints
```

## `scripts/reset.sh`

Should reset deterministic Phase 1 state:

```text
tool execution counters
approval test state
fault state
local test artifacts
```

## `scripts/preflight.sh`

Should check:

```text
azd ai agent doctor
authentication
required RBAC
Hosted Agent reachable
Toolbox reachable
tools/list succeeds
dns_resolution smoke test succeeds
APIM endpoint reachable
```

Exit non-zero on failure.

---

# 11. Tests to Implement

Create tests or executable validation scripts for:

```text
spike01_history_session
spike02_toolbox_allow
spike02_toolbox_block
spike03_approval_approve
spike03_approval_deny
spike03_approval_binding
spike04_affinity
spike04_new_session_control
spike04_sse
```

Mocks may be used for local unit tests, but the Phase 1 result must depend on real integration validation.

---

# 12. Evidence Capture

For every spike, save evidence under:

```text
evidence/
```

Evidence should contain, where applicable:

```text
commands executed
timestamps
exit codes
relevant logs
trace IDs
conversation IDs
session IDs
HTTP headers relevant to affinity
tool execution counters
stream chunk timestamps
package versions
```

Do not store secrets.

---

# 13. PHASE1_REPORT.md

Prepare a report template but do not mark PASS until validation is complete.

Required structure:

```text
# Phase 1 Runtime Validation Report

## Environment
- date
- subscription/project
- region
- package versions
- Terraform provider versions

## Spike 1
Status: NOT VALIDATED / PASS / FAIL
Evidence:
...

## Spike 2
Status: NOT VALIDATED / PASS / FAIL
Evidence:
...

## Spike 3
Status: NOT VALIDATED / PASS / FAIL
Evidence:
...

## Spike 4
Status: NOT VALIDATED / PASS / FAIL
Evidence:
...

## Architecture Unfreeze Required?
YES / NO

## Phase 1 Result
NOT COMPLETE / PASS / BLOCKED
```

---

# 14. Construction Completion Criteria

The construction task is complete only when:

```text
[ ] minimal Foundry Hosted Agent deploys
[ ] Responses 2.0.0 configured
[ ] history_source="agent_server" configured
[ ] store=False configured

[ ] AgentSession test state implemented
[ ] TodoProvider / AgentModeProvider minimally composed

[ ] Toolbox tool is real and callable
[ ] Function Middleware can inspect calls
[ ] block mechanism is implemented

[ ] R2 approval flow is implemented
[ ] approve and deny paths exist
[ ] execution counters exist

[ ] Stable/Candidate backends exist
[ ] APIM weighted pool configured
[ ] session affinity configured
[ ] SSE configuration applied

[ ] reset/deploy/preflight scripts exist
[ ] validation scripts exist
[ ] evidence directory exists
[ ] PHASE1_REPORT.md template exists
```

At the end, do NOT claim that Phase 1 passed.

State only:

```text
PHASE 1 CONSTRUCTION COMPLETE
READY FOR INDEPENDENT VALIDATION
```

unless the separate validation procedure has actually been executed.
