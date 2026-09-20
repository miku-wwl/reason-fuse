# Hosted concurrency correction plan

Baseline: `e2dc162b5988fe3542278f2d3b8f0325d49bf8a5`, pushed to GitHub main
and verified against the remote on 2026-09-21 (Pacific/Auckland).
The previous cloud gate remains FAIL; its evidence is immutable historical input.

## Objective and scope

Prevent two requests in one supported Hosted conversation from obtaining separate
execution authority or overwriting the retained obligation/containment. Preserve
native approval, runtime completion, streaming interception, dependency pins and
the existing single-agent architecture. No benchmark starts during this correction.

## Execution sequence

1. Reproduce the explicit-conversation race through the actual pinned
   ResponsesHostServer request lifecycle, including restoration and persistence.
   Distinguish native task admission from handler execution and state saving.
   A primitive-only probe is insufficient: the SDK primitive currently queues
   explicit inputs correctly in a local probe, while the deployed host did not.
2. Identify the smallest enforcement point before session restoration/dispatch.
   Prefer existing native storage/task coordination. Do not rely on a second
   per-Python-object lock or assume that one logical ID means one live object.
   Failed admission/storage and cancellation must not admit a stale successor.
3. Add regressions with independent restored sessions and a backend that accepts
   every dispatch. Cover both explicit conversation and previous-response chains,
   duplicate approvals, stale continuations, failed persistence and cancellation.
   Retain the existing local tests and run relevant checks before deployment.
4. Deploy an allowlisted source package to the existing Foundry project. Recreate
   only the temporary Operations fixture required for the cloud gate. Record the
   exact package, version and observed request/session coordination identity.
5. First rerun CLOUD-11 on both paths with independent attempt counters. If fixed,
   rerun CLOUD-1 through CLOUD-12 where hosting behavior can be affected, including
   denial, streaming, FAILED/UNKNOWN and native-reapproved replay. Keep actual
   evidence separate from local tests and source inference.
6. Publish a new correction report with PASS/FAIL and remaining boundaries; clean
   up resources created solely for the gate. Keep historical FAIL evidence intact.

## Acceptance

Two overlapping approvals must result in at most one backend dispatch, independent
of backend deduplication. A successor must see the authoritative updated state;
pending verification and containment must not be lost. No unsupported operational
success may escape, and native approval remains the only execution authorization.
Cloud PASS requires real evidence for every affected path, not a passing unit test
or a narrower un-enforced scope statement.

The requested first push is complete. Changes produced by this execution will be
reported with their validation status; the historical cloud FAIL is not rewritten.

## Execution findings (2026-09-21)

- Diagnostic v9 reproduced two backend dispatch attempts from overlapping native
  approvals. Two subsequent overlapping reads showed the same native conversation
  and chain, distinct responses, and `is_steered_turn=false` for both. The transport
  preserves conversation identity; enabling native steering did not enforce the
  needed exclusion in the observed cloud path. The precise SDK/service internals
  causing that admission failure are not established by these logs.
- Candidate v10 adds a native Foundry State Store admission record with atomic
  creation and ETag conditional writes. It owns restore, dispatch and session save.
  Response aliases bind previous-response continuations to the same record; stale
  heads fail before restoration. Steering is disabled to avoid cancelling an
  admitted effect. Pinned native tasks retain their existing lifecycle role.
- Admission records never expire or transfer automatically. Cancellation, an
  incomplete/failed host response, storage errors or missing saved AgentSession
  block continuation pending reconciliation. Existing previous-response chains
  without admission records are rejected; validation uses fresh conversations.
  This favors containment over availability and is not distributed exactly-once.
- 100 local tests pass, including eight new tests through the actual pinned host
  or native conditional store. Local task scheduling is disabled for those host
  tests so it cannot mask an admission defect. The fake backend accepts every
  dispatch, and two independently restored AgentSession objects are observed.
- Cloud evidence is separate under `docs/evidence/p0-foundry/hosted-concurrency/`.
  v10 CLOUD-1 through CLOUD-12 PASS; the historical v7/v8 gate remains FAIL.
  Both concurrent approval paths record one dispatch and one admission rejection.
  The completed [correction report](evidence/p0-hosted-concurrency-validation.md)
  records deployment, streaming, containment, usage and cleanup evidence.

The [native storage documentation](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-state-store)
describes user isolation, ETag preconditions and configurable expiry. Those API
features motivate the bounded change; only the deployed tests can establish the
observed competition deployment behavior.
