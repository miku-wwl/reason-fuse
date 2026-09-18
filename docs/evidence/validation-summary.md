# ReasonFuse submission validation summary

This index separates local proof from bounded cloud proof for the final
Microsoft Agent-a-thon submission.

## Status matrix

| Capability | Result | Evidence |
|---|---|---|
| Frozen ReasonFuse core behavior | PASS | Existing tests and local boundary checks |
| Local Foundry Local inference/function calling | PASS | [`foundry-local-e2e.json`](foundry-local-e2e.json) |
| Local approval and outcome branches | PASS | `VERIFIED`, `FAILED`, and `UNKNOWN` in the local report |
| Local containment/no replay | PASS | Local report and existing tests |
| Hosted Agent deployment | PASS | [`cloud-e2e.md`](cloud-e2e.md) |
| Hosted Agent normal multi-turn | PASS | [`cloud-e2e.md`](cloud-e2e.md) |
| Hosted native approval boundary | PASS | No execution before approval in [`cloud-e2e.md`](cloud-e2e.md) |
| Hosted accepted action + fresh outcome | PASS | `accepted=true`/`202` → fresh `HEALTHY/g2` → `OUTCOME_VERIFIED` |
| Hosted containment/no replay | PASS | `NO_PROGRESS` → `BLOCK`, side-effect count remains `1` |
| Application Insights / cloud custom tracing | NOT CONFIGURED | No cloud telemetry claim |
| Foundry IQ native retrieval | NOT VALIDATED | Outside bounded submission scope |
| APIM/canary | REMOVED FROM FINAL SCOPE | Not a submission dependency |
| Production Operations backend | NOT CLAIMED | Validation fixture only |
| Final video | PENDING | Human presentation step |

## Local evidence

The local real-model audit used Foundry Local CLI `0.10.3` with `phi-4-mini`.
It recorded PASS for real function calling, native approval,
`OUTCOME_VERIFIED`, `POSTCONDITION_FAILED`, `OUTCOME_UNKNOWN`, containment,
blocked-host validation, and no replay. This is LOCAL-ONLY evidence; it does
not prove Hosted Agent or Azure platform behavior.

The repository's deterministic local checks are intentionally small. The
15-scenario file is a human-readable fault-scenario list, not a 300-run
benchmark, load test, or model-quality evaluation.

## Cloud evidence

The bounded cloud run used Hosted Agent `reasonfuse:6`, Responses `2.0.0`, and
`gpt-5-mini`. It proved the approval boundary, exactly-once accepted restart,
fresh postcondition verification, and no-progress containment. The temporary
Operations MCP resources were deleted after evidence capture. The source
remains under `cloud/operations-mcp/` for a future bounded reproduction.

The normal Hosted request contract used `store=False`. The approval continuation
used `store=True` temporarily because a `previous_response_id` continuation
requires server-side response state. This distinction is preserved in the
cloud evidence and is not presented as a `store=False` approval-continuation
pass.

## Reproducibility boundary

The evidence is intentionally compact and judge-facing. It does not include
secrets, tokens, temporary cloud hostnames, or credential caches. Detailed raw
Azure reports remain local-only. No new Azure resource is required for local
review, and no large benchmark is part of the final submission scope.
