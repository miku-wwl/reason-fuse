# ReasonFuse Competition RC1 — Recovery Runbook

## Operating rule

Start with read-only checks. Do not destroy infrastructure as a recovery step.
The default recovery command is:

```powershell
.\scripts\emergency_recover.ps1 -Mode local
```

The Hosted check mode does not change APIM or Azure:

```powershell
.\scripts\emergency_recover.ps1 -Mode hosted-check
```

## Symptoms and safe actions

| Symptom | Check | Safe action | Verification |
| --- | --- | --- | --- |
| Local demo has stale state | Run `demo/reset.ps1` | Reset local fixture/session state | `PHASE4_RESET_PASS` |
| Local preflight fails | Run `scripts/phase5_preflight.ps1` | Fix the reported local dependency or source issue | `PHASE5_PREFLIGHT=PASS` |
| Agent endpoint is unavailable | Check Hosted endpoint and deployment status | Do not change code first; inspect `azd`/Foundry deployment status | Hosted endpoint returns a release probe |
| Toolbox is unavailable | Run Toolbox smoke/read-only `tools/list` check | Restore the frozen Toolbox endpoint/configuration | Expected pinned tools are listed |
| APIM routing is wrong | Read the canary pool and cookie configuration | Restore the documented frozen weights through the authorized Hosted runbook | Stable/Candidate weights and affinity match manifest |
| Affinity is lost | Inspect `ReasonFuseAffinity` cookie and conversation IDs | Start a new client; do not claim an existing session migrated | Same client remains on one release |
| SSE is buffered | Inspect APIM policy and response timing | Restore the no-buffering policy only after review | Chunks arrive before final completion |
| Judge Mode is unavailable | Call the runtime-state path | Use the retained report and local demo until Hosted recovery is authorized | Runtime fields map to actual state |
| Application Insights is delayed | Check ingestion timestamp and correlation ID | Wait for bounded ingestion; do not fabricate trace PASS | APIM request and ReasonFuse trace correlate |
| Candidate still receives traffic after rollback | Read the APIM pool | Set Candidate to zero only in an authorized Hosted operation | New sessions route Stable |
| Operations API has dirty state | Run the supported reset path | Reset the disposable test service/state | `BEFORE`/`AFTER` sequence is clean |
| Deployment drift is suspected | Compare release manifest, `azure.yaml`, Terraform and lock files | Stop the demo and review the diff | Manifest and deployed values agree |

## Escalation boundary

If a recovery requires a new architecture, a new service, destructive deletion,
or a dependency upgrade, stop and record the issue in `KNOWN_LIMITATIONS.md` and
the Phase 5 verification open-questions report.
