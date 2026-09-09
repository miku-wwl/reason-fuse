# Phase 2 ReasonFuse Core Validation Report

## Decision

`PHASE 2 RESULT: PASS`

This is an independent Phase 2 P0 validation result for the documented
deterministic runtime scope. It is not a claim that Foundry IQ, a production
Operations backend, cloud Core span export, or concurrent/forked execution has
been proven. Those boundaries are listed in the separate
[open-questions report](verification-open-questions.md).

The construction handoff at [report.md](report.md) and its
[index](../../../evidence/phase-02-core/index.json) were retained unchanged.
The independent batch and its complete hashed index are:

- [independent batch index](../../../evidence/phase-02-core/verification-20260909T110000Z/index.json)

## Environment

Validation ran from `D:\workshop\sep\reason-fuse` against the existing
Australia East resources. The final captured deployment was restored to the
default ON configuration before the final reset:

| Item | Verified value |
| --- | --- |
| Batch | `verification-20260909T110000Z` |
| Region | `australiaeast` |
| Model | `gpt-5-mini`, version `2025-08-07` |
| Agent framework | `agent-framework-core 1.17.0`; `agent-framework-foundry 1.12.0` |
| Hosting / SDK | `agent-framework-foundry-hosting 1.0.0b260903`; `azure-ai-projects 2.3.0`; `azure-ai-agentserver-responses 2.2.0b1` |
| Python | local `3.13.9`; hosted runtime `3.13.15` |
| Toolbox | version `13` |
| Agents | stable version `35`, candidate version `15`, both active |
| Profile | `phase2` |
| Final enabled state | `true` on both agents |
| Final contract | `{}` on both agents |
| Source manifest | `8b8c1247360c93469bfc982920136d2adc0ec8dd800ea1bb286927712773b11e` |
| Audited ZIP SHA-256 | `3c655e50c5d8be97527069444adb7961769c09519fd5cdcf5ec340696163e04a` |
| Final package identity | both agents reported the audited ZIP hash |

The full environment readback is [environment.jsonl](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T021543482005Z-environment.jsonl), and the package identity is [source-identity.jsonl](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T013808121874Z-source-identity.jsonl). Message-content capture remained disabled.

The independent local gates passed:

- 36 unit tests: [unit recorder](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T004018886191Z-verification-20260909T110000Z-00-unit.jsonl)
- [LOCAL_CORE](../../../evidence/phase-02-core/local-20260909/20260909T004027446692Z-local-core.jsonl)
- [LOCAL_INTEGRATION / Operations API](../../../evidence/phase-02-core/local-20260909/20260909T004034569000Z-operations-api.jsonl)

## Process and fixed trial plan

The independent runner performed a fresh audited deployment, preflight and
reset, configuration-separated OFF/ON trials, detector and outcome repeats,
clean-start redeployment, clean-start revalidation, final default-ON restore,
and a final reset after the compatibility gate. Shared counters were reset
between trials; fresh conversations were used for each hosted scenario.

The fixed hosted plan was:

| Scenario | Required independent attempts | Result |
| --- | ---: | --- |
| `a-off` | 2 | 2 PASS |
| `b-on` | 2 | 2 PASS |
| `c-exact` | 3 | 3 PASS |
| `d-oscillation` | 3 | 3 PASS |
| `e-retrieval` | 3 | 3 PASS |
| `f-useful` | 4 | 4 PASS, including clean-start |
| `g-outcome-failure` | 4 | 4 PASS, including clean-start |
| `h-budget` | 1 | 1 PASS |
| `i-outcome-unknown` | 2 | 2 PASS, including clean-start |
| `j-database-recheck` | 1 | 1 PASS |

The index records every attempt, command recorder, source identity, audited
package, final environment and reset artifact with SHA-256. It contains 69
supporting command/deployment recorders.

## OFF Baseline

`PASS`

The same no-progress DNS input executed four redundant calls with
`reasonfuse_enabled=false`, no fuse reason, no containment, and an explicit
harness stop. The external counter reached four executions. The clean-start
OFF repeat also passed.

Evidence: [initial A OFF](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T005324455475Z-hosted.jsonl), [clean-start A OFF](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014329013340Z-hosted.jsonl).

## ON No-Progress

`PASS`

With the same bounded input, model, tools and reset world, ON mode executed two
calls and then contained the next redundant proposal with `NO_PROGRESS`.
Objective progress remained false. The clean-start ON repeat also passed.

Evidence: [initial B ON](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T005557944795Z-hosted.jsonl), [clean-start B ON](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014600687040Z-hosted.jsonl).

## Exact Loop

`PASS`

The isolated contract raised the stall and objective-progress intervals to 20.
Three independent fresh-conversation trials produced stable canonical
fingerprints and `EXACT_LOOP`; two calls executed and the third proposal was
blocked in each trial.

Evidence: [C1](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T005816509811Z-hosted.jsonl), [C2](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T005915513492Z-hosted.jsonl), [C3](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T010018766270Z-hosted.jsonl).

## Oscillation

`PASS`

The alternating API/payments DNS pattern produced `OSCILLATING` consistently
across three resets. The final proposal was blocked, and the completed calls
were preserved as executed rather than mislabeled as prevented.

Evidence: [D1](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T010123913345Z-hosted.jsonl), [D2](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T010243879869Z-hosted.jsonl), [D3](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T010402620271Z-hosted.jsonl).

## Retrieval Churn

`PASS`

The deterministic Toolbox retrieval fixture returned equivalent normalized
evidence for semantically different queries. All three repeats reached
`RETRIEVAL_CHURN`. This proves the implemented normalization/churn behavior for
the fixture; it does not prove Foundry IQ integration.

Evidence: [E1](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T011758513544Z-hosted.jsonl), [E2](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T011905994832Z-hosted.jsonl), [E3](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012011209378Z-hosted.jsonl).

## Useful Recheck

`PASS`

Both health-tool paths passed. `service_status` (F) and `database_health` (J)
performed a health read, an accepted restart, and a fresh bound verification
read. The second read was marked `useful_recheck=true`, was allowed, and the
successful case returned `OUTCOME_VERIFIED`. F was repeated three times plus a
clean-start run; J was run independently once.

Evidence: [F1](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012127403660Z-hosted.jsonl), [F2](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012248215748Z-hosted.jsonl), [F3](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012408893176Z-hosted.jsonl), [F clean-start](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014714117432Z-hosted.jsonl), [J](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012527127369Z-hosted.jsonl).

## Run Contract

`PASS`

The local boundary suite passed the frozen limits, invalid-limit rejection,
step/progress boundaries, side-effect reservation, pending postcondition and
diagnostic-read behavior. Hosted H used 45-second pacing, executed exactly ten
DNS calls, and blocked proposal eleven with `BUDGET_EXHAUSTED`; no additional
external tool was dispatched.

Evidence: [local core recorder](../../../evidence/phase-02-core/local-20260909/20260909T004027446692Z-local-core.jsonl), [H budget](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T010518017858Z-hosted.jsonl).

## Outcome Failure

`PASS`

The accepted restart whose service remained unhealthy produced
`POSTCONDITION_FAILED`, not success. Subsequent dispatch was contained. Three
normal repeats and one clean-start repeat passed.

Evidence: [G1](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012644041360Z-hosted.jsonl), [G2](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012742767895Z-hosted.jsonl), [G3](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012841906768Z-hosted.jsonl), [G clean-start](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014835328411Z-hosted.jsonl).

## Outcome Success

`PASS`

The useful recheck paths observed a fresh healthy postcondition after the
accepted restart and returned `OUTCOME_VERIFIED`. This is the deterministic
Operations fixture success path, not proof of a production restart backend.

Evidence: [F useful recheck](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012127403660Z-hosted.jsonl), [J database recheck](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012527127369Z-hosted.jsonl).

## Outcome Unknown

`PASS`

The stale/inconclusive health observation path returned `OUTCOME_UNKNOWN` and
contained subsequent external dispatch. The normal and clean-start trials both
passed.

Evidence: [initial I](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T012947678021Z-hosted.jsonl), [clean-start I](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014932721791Z-hosted.jsonl).

## Todo-Only Progress Negative Control

`PASS` as a LOCAL_CORE negative control.

The local boundary tests prove a Todo transition can produce `todo_delta` while
`objective_progress` remains false. The hosted no-progress and detector trials
also retained `progress_state` and evidence state in live runtime state rather
than trusting model prose.

Evidence: [LOCAL_CORE](../../../evidence/phase-02-core/local-20260909/20260909T004027446692Z-local-core.jsonl) and the runtime state embedded in [B ON](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T005557944795Z-hosted.jsonl).

## Middleware Enforcement

`PASS`

Hosted detector evidence shows middleware `BEFORE`/`AFTER` state, completed
calls preserved as executed, and blocked proposals not increasing the external
Operations counters. The compatibility gate separately passed native approval
approve/deny/binding/replay checks and interception/API path checks.

Evidence: [D1 middleware evidence](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T010123913345Z-hosted.jsonl), [compatibility batch](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T015306886049Z-batch-verification-20260909T110000Z-compatibility.jsonl).

## Determinism Repeats

`PASS` for the required independent hosted plan.

Exact Loop, Oscillation, Retrieval Churn, Useful Recheck, and Outcome Failure
were repeated according to the fixed plan. Fresh conversations and reset epochs
were used between attempts. Every required attempt is retained in the index;
there were no failed hosted attempts hidden by selecting an earlier PASS.

The exact per-scenario counts are in the [independent index](../../../evidence/phase-02-core/verification-20260909T110000Z/index.json).

## Clean-Start Revalidation

`PASS`

A fresh full audited deployment was performed before clean-start validation.
Clean-start OFF, ON, Useful Recheck, Outcome Failure and Outcome Unknown all
passed. The clean-start deployment reported stable version 33 / candidate 15,
Toolbox 13, and the same audited package hash on both agents. The final
default-ON restore was performed after the campaign, followed by final
environment capture and reset.

Evidence: [clean-start A](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014329013340Z-hosted.jsonl), [clean-start B](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014600687040Z-hosted.jsonl), [clean-start F](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014714117432Z-hosted.jsonl), [clean-start G](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014835328411Z-hosted.jsonl), [clean-start I](../../../evidence/phase-02-core/verification-20260909T110000Z/20260909T014932721791Z-hosted.jsonl).

## Compatibility Regression Gate (Phase 1)

`PASS`

This was run as a separate compatibility gate, not substituted for the Phase 2
detector trials. The 14-command suite passed, including preflight, identity,
history/session, toolbox interception, approval, APIM affinity, SSE, metadata
telemetry, and the fixed 60-client routing control. The routing control ended
with 57 stable and 3 candidate selections.

Evidence: [compatibility batch](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T015306886049Z-batch-verification-20260909T110000Z-compatibility.jsonl) and its [command recorder](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T015305797971Z-verification-20260909T110000Z-54-compatibility.jsonl).

## Final Default-ON Restore and Scoped Reset

`PASS`

After compatibility, the environment was captured with both agents active,
`REASONFUSE_ENABLED=true`, profile `phase2`, contract `{}`, and the same package
hash. A final reset then returned counters to zero, restored the baseline world
and removed recorded test sessions. The reset was performed after the last
compatibility client, so its readback covers the complete campaign.

Evidence: [final environment](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T021543482005Z-environment.jsonl), [final reset](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T021517872355Z-reset.jsonl).

## Fixes and Retests

Two setup/execution issues were retained and classified rather than hidden:

1. The first unit command omitted `PYTHONPATH=src` and failed with
   `ModuleNotFoundError: No module named 'reasonfuse'`. Classification:
   `CONFIGURATION_ERROR`. The runner was corrected to set `PYTHONPATH`, and the
   rerun passed all 36 tests.
2. The first fresh deployment encountered an Azure CLI token acquisition
   timeout (`get-access-token --resource https://ai.azure.com`, 10-second
   timeout). Classification:
   `EXTERNAL_SERVICE_OR_QUOTA_FAILURE`. A token refresh/retry was performed;
   the audited deployment then passed and all downstream gates were rerun.

Evidence: [unit setup failure](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T003525066496Z-verification-20260909T110000Z-00-unit.jsonl), [deployment setup failure](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T003626961945Z-verification-20260909T110000Z-03-deploy-initial.jsonl), and the passing [unit retest](../../../evidence/phase-01-runtime-validation/runs/20260909/20260909T004018886191Z-verification-20260909T110000Z-00-unit.jsonl).

The only code/tooling change made during this validation was a narrow fix to
the independent indexer so it records the audited binary ZIP as a hashed file
artifact instead of attempting to decode it as JSONL. No ReasonFuse runtime
source behavior was changed by that fix.

## Evidence Boundaries

The following remain `NOT VERIFIED` and are not silently promoted to PASS:

- Foundry IQ native retrieval integration; Hosted E used a deterministic
  Toolbox fixture.
- Production Operations restart/health semantics; Hosted F/G/I used the
  deterministic Operations API fixture.
- Cloud collector correlation for `reasonfuse.*` Core spans; local emission and
  hosted decision state were verified separately.
- Concurrent or forked turns, cold-start recovery, and multi-action P0
  postcondition concurrency.

The evidence also does not attempt to retain secrets, cookies or message bodies;
message-content capture was disabled.

## Architecture Change Required?

`NO` for the validated P0 scope. No architecture assumption failed, and no
resource teardown or alternate transport was introduced.

## Phase 2 Result

`PASS`

The independent hashed index reports
`INDEPENDENT_PHASE2_VALIDATION_PASS`. All required P0 gates passed, the clean
start passed, compatibility passed, default ON was restored, and the final
scoped reset passed.
