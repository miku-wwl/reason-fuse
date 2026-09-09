# Phase 3 Evidence Benchmark — Independent Verification Report

## Result

`PHASE 3 RESULT: PASS`

The repaired v2 benchmark satisfies the deterministic Phase 3 exit gate. The
previous block was resolved by replacing the repeated-template dataset with
20 explicit semantic pattern families per category and by adding a real
Todo-only negative-control scenario. The result is still bounded to the local
deterministic fixture; it is not a production or hosted-agent accuracy claim.

The detailed execution artifacts were temporary validation outputs. The
results below are retained as conclusions and can be reproduced from the
dataset and verification scripts when needed; raw evidence files are not part
of the long-term deliverable.

## Gate summary

| Gate | Result | Evidence |
| --- | --- | --- |
| Dataset count and schema | PASS | 100 records, unique IDs, five categories at 20 each; portable validator passed |
| Dataset quality/diversity | PASS | 20 explicit semantic pattern families in every category; unique domains, resources, query intents, or postcondition dimensions |
| Runner integrity | PASS | 300 valid records, no invalid runner rows, reset and fresh-state checks passed |
| 300-run completion | PASS | 300 raw and 300 normalized records; every scenario has repetitions 1, 2, 3 |
| Ground-truth consistency | PASS | Independently compared expected and actual trip, failure, outcome, useful-recheck, and healthy-completion fields |
| Confusion matrix | PASS | Independently recomputed TP=240, FP=0, TN=60, FN=0 |
| Core metrics | PASS | Recall, precision, FPR, FNR, accuracy and F1 independently match the batch report |
| Healthy preservation | PASS | 60/60 Healthy runs completed without containment |
| Todo-only negative control | PASS | H-018 runs 3 times per batch; Todo changes produce `todo_delta=true` but `objective_progress=false` and do not trip |
| Useful recheck preservation | PASS | 12/12 expected useful rechecks preserved |
| Postcondition failure detection | PASS | 60/60 detected as `POSTCONDITION_FAILED` |
| OFF/ON comparison | PASS | 20 controlled pairs with identical scenario/world/version inputs |
| FoundryEvals | PARTIAL / model execution complete | Offline `F1ScoreEvaluator` passed 300/300 labels; real Azure `ToolCallAccuracyEvaluator` completed 300/300 cases with 0 transport/evaluator errors; model threshold score was 159/300, so this is execution-complete evidence, not a claim that every generated trajectory is accurate |
| Microbenchmark | PASS | Independent rerun completed 10,000 events with network disabled and no LLM |
| Reproducibility | PASS | 10 representative cases, two per category, reproduced classifications |
| Phase 2 regression | PASS | 36/36 unit tests and Phase 2 artifact check passed |

## Independent recomputation

The verifier read the v2 raw JSONL rather than trusting the generated summary:

```text
raw runs                         300
valid                            300
invalid                          0
unique (scenario,repetition)     300
repetitions per scenario         1, 2, 3
```

Recomputed confusion matrix and metrics:

```text
TP = 240
FP = 0
TN = 60
FN = 0
Recall = 1.0
Precision = 1.0
FPR = 0.0
FNR = 0.0
Accuracy = 1.0
F1 = 1.0
```

The perfect result is internally consistent, but remains a deterministic
fixture result rather than a production generalization claim.

## Diversity repair

The repaired v2 dataset records a required `fault_configuration.pattern_family`
for every scenario. The independent verifier found 20 unique semantic
families in every category:

| Category | Semantic pattern families | What varies materially |
| --- | ---: | --- |
| Healthy | 20 | useful rechecks, evidence accumulation, resource/world changes, interrupted loops, and Todo-only negative control |
| Exact Loop | 20 | target-specific canonical tool proposals across DNS, service, database, config, deployment, dependency, and runtime probes |
| Oscillation | 20 | distinct two-probe pairs across diagnostic classes and named service/resource domains |
| Retrieval Churn | 20 | distinct incident domains, three different query intents, and one domain-specific normalized evidence signature per case |
| Outcome Failure | 20 | distinct services, postcondition states, generation IDs, and verification tools |

Retrieval Churn still intentionally uses `retrieval_search` as its tool name;
the meaningful variation is the domain/query/evidence identity, not a fake
tool-name change. The raw tool-shape count is therefore 1 for that category,
while the semantic pattern-family count is 20.

## Todo-only negative control

H-018 contains three actions:

```text
OPEN -> IN_PROGRESS -> COMPLETED
```

Each action changes only the persisted Todo snapshot. The raw state evidence
shows `todo_delta=true`, `objective_progress=false`, no containment, and zero
objective-progress events. This independently exercises the Phase 2 invariant
that planning state is not objective evidence.

## Reset and raw-record audit

All 300 records contained `RESET_COMPLETE`, `network=DISABLED`,
`fixture_scope=true`, zero reset counters, fresh run/conversation/session IDs,
and a first persisted state with `event_count=1`. No row was classified as a
runner, environment, model, tool, timeout, or reset failure. Tokens and cost
remain `NOT AVAILABLE`; `NOT_AVAILABLE_LOCAL` is not cloud trace evidence.

## FoundryEvals and explicit boundaries

The environment initially lacked both `azure.ai.evaluation` and a top-level
`foundry` Python module. The compatible `azure-ai-evaluation==1.18.5` package
was then installed into the local validation environment. Its offline
deterministic `F1ScoreEvaluator` completed 300 expected-vs-actual
classification checks with 300/300 passing. The supported project stack was
also present (`azure.ai.projects`, `agent_framework.foundry`, and the Azure
AI/Foundry CLI extensions); the unrelated PyPI package named `foundry` was
deliberately not used.

The repository did have a usable Azure model configuration. `azure.yaml`
declares the `gpt-5-mini` deployment (model version `2025-08-07`) and the
Phase 2 verification record identifies the deployment region as
`australiaeast`. A read-only Azure deployment check returned state
`Succeeded`. The first model-backed attempt exposed an SDK compatibility
issue: the evaluator sent `max_tokens`, while this reasoning model requires
`max_completion_tokens`. The evaluator was rerun with the SDK's
`is_reasoning_model=True` compatibility path and reached the real Azure model.

The initial bounded model-backed run used two representative cases per
category. It was then extended to the complete 100 scenarios x 3 repetitions
using the configured Azure deployment:

```text
evaluator       ToolCallAccuracyEvaluator
deployment      gpt-5-mini
region          australiaeast
initial subset  10 cases (2 per category), 10/10, 0 errors
full run        300 cases (100 scenarios x 3 repetitions)
completed       300/300 after four low-concurrency retries
errors          0 in merged final artifact
threshold pass  159/300 (score >= 3)
deployment      gpt-5-mini / australiaeast / 2025-08-07
transport       direct Azure OpenAI transport using the evaluator's validated prompt
```

The merged model result was 300/300 completed with four low-concurrency
retries; the raw model artifact is intentionally not retained in the slim
deliverable.

The redacted live deployment check is captured in the command-evidence
directory under the `phase3-v2-independent-model-deployment-check-query`
run; it returned `gpt-5-mini`, version `2025-08-07`, `GlobalStandard`, and
`Succeeded`.

This proves complete model-backed evaluator reachability and execution. The
quality-layer status remains `PARTIAL` because the project does not expose a
top-level `foundry` module/cloud Foundry evaluation orchestration in this
environment, and because 159/300 model judgments met the evaluator threshold.
The deterministic Phase 3 gate remains `PASS`; the full model artifact is an
additional quality result, not a replacement for the deterministic gate.

The following remain outside this Phase 3 evidence claim:

```text
Foundry IQ native retrieval       NOT VERIFIED (project connections = 0; no native knowledge source configured)
production Operations backend     PASS (live hosted agent -> Toolbox -> Operations Web App allow/block and approval evidence)
cloud Core trace correlation      PASS (APIM SSE request operation ID matched Log Analytics AppRequests)
concurrent/forked turns           PASS (4-way concurrency and 2-way canonical-conversation fork)
fresh-client recovery proxy       PASS (new client restored prior conversation state)
cold-start recovery               NOT VERIFIED (no platform restart/cold-start was forced)
```

Foundry IQ and true platform cold-start remain outside the verified boundary;
the reachable production Operations, trace, concurrency/fork, and
fresh-client recovery proxy now have current hosted evidence.

The hosted boundary checks were executed successfully. Their raw request
logs are temporary and are not retained in the slim deliverable. The
conclusion remains: Operations, trace correlation, concurrency/fork, and
fresh-client recovery proxy passed; Foundry IQ native retrieval and true
cold-start remain not verified.

## Verification command evidence

Two initial helper invocations were environment errors: the reproduction
helper lacked the repository `src` path, and the standalone microbenchmark
command lacked `PYTHONPATH=src`. Both helpers were corrected and rerun
successfully. They did not affect the construction records or the final PASS.

## Final determination

The previous diversity and Todo-coverage blockers are resolved. The full
model-backed evaluator and reachable hosted production boundaries are now
evidenced. Phase 3 passes its deterministic evidence gate; FoundryEvals
remains `PARTIAL`, while Foundry IQ native retrieval and true cold-start
remain explicitly `NOT VERIFIED`.
