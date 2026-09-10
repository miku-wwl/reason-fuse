# Phase 4 Hosted Verification Report

## Scope

- Region: `australiaeast`.
- Fresh validation environment: `rf-phase4c-20260910`, resource group `rg-reasonfuse-phase4c-aue`; removed after verification.
- The run used one bounded Native IQ source and one gpt-5-mini call per required hosted probe.
- Raw JSONL evidence was kept outside the repository during execution and removed after this summary. No secrets or tokens were retained.

## Results

| Gate | Result | Evidence |
| --- | --- | --- |
| Native Foundry IQ direct retrieval | **PASS** | Search index `reasonfuse-phase4-index`, Knowledge Source `reasonfuse-phase4-ks`, Knowledge Base `reasonfuse-phase4-kb`, source key `rf-phase4-iq-001`, citation and `searchIndex`/`agenticReasoning` activity. |
| Stable Agent Native IQ MCP | **PASS** | Hosted Stable version 2 emitted `function_call: foundry_iq___knowledge_base_retrieve`; output contained `mcp://searchindex/rf-phase4-iq-001` and the containment answer. |
| Candidate Agent Native IQ MCP | **PASS** | Hosted Candidate version 2 emitted the same Native IQ MCP function through the shared versioned Toolbox and returned the same source/citation. |
| Foundry project connection | **PASS** | `RemoteTool` + `ProjectManagedIdentity` connection was accepted and referenced by the Toolbox `MCPToolboxTool`. |
| APIM weighted canary | **PASS** | Live pool readback and clean-start start state: Stable 95 / Candidate 5. |
| APIM session affinity | **PASS** | One persistent client stayed on Stable across turns; a fresh client received an independent Stable assignment. Cookie: `ReasonFuseAffinity`. |
| APIM SSE | **PASS** | 52 SSE lines/chunks arrived incrementally; first chunk about 7.9s, final completion about 22.5s. |
| Real Operations | **PASS** | Real APIM call invoked `operations___dns_resolution`; runtime state contained authoritative `BEFORE`/`AFTER` middleware events and telemetry flags. |
| Candidate regression | **PASS** | Stable: DNS `INCONCLUSIVE` → `service_status`, `PROGRESS`; Candidate: repeated DNS → `NO_PROGRESS`, `STALLED`, `contained=true`. |
| Rollback | **PASS** | APIM changed to Stable 100 / Candidate 0; a new conversation routed to Stable version 2. |
| Clean-start E2E | **PASS** | Fresh Terraform/azd environment completed preflight, Judge Mode runtime-state read, four signature demos once, hosted regression, rollback and Stable recovery. |
| Managed hosted-session cold-start | **PASS** | Prior bounded hosted-session test used the official stop/resume lifecycle; state and turn continuity were restored. |
| Cloud trace correlation | **PASS** | Prior bounded cloud run correlated APIM `AppRequests` with ReasonFuse `AppTraces` and `reasonfuse_*` fields. |

## Native IQ end-to-end proof

The deployed Stable and Candidate agents used the same versioned Foundry Toolbox. Its `tools/list` included `foundry_iq___knowledge_base_retrieve`, backed by the Foundry project RemoteTool connection. Both Hosted Agent responses contained a real function call, a tool output with source key `rf-phase4-iq-001`, and a grounded answer identifying `BLOCK` and `service_status`. This is not the deterministic `retrieval_fixture`.

Microsoft documents this pattern as a Foundry project `RemoteTool` connection using the project's managed identity for the Azure AI Search Knowledge Base MCP endpoint ([Foundry IQ connection guidance](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/foundry-iq-connect)) and recommends toolboxes for reusable MCP authentication/configuration ([MCP/toolbox guidance](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/model-context-protocol)).

## Clean-start E2E proof

The final successful run began by restoring the live APIM pool to 95/5, then ran the sequence without code edits:

```text
fresh environment → preflight → Judge Mode runtime_state
→ OFF/ON → Unknown Correct Path → Outcome Failure
→ Stable/Candidate regression → rollback → Stable recovery
```

The four local signature demos were each reset and executed once in this clean-start sequence; their existing three-run local repeatability remains recorded in `PHASE4_REPORT.md`. The hosted Candidate regression was independently caused by the Candidate release instruction; the ReasonFuse middleware and run contract were shared.

## Runtime caveats

- The first APIM conversation request immediately after deployment returned a transient 504 during platform warm-up. After the deployment became active, the same endpoint returned 200; the final clean-start run passed. This is recorded as an environment warm-up observation, not hidden.
- The current evidence is bounded P0 validation for the fixed competition profile.

## Conclusion

The two previously open implementation/verification items are resolved for the bounded Phase 4 scope: Stable/Candidate now perform real Native Foundry IQ MCP calls, and the complete clean-start E2E sequence passes in a fresh Azure environment.
