# ReasonFuse Competition RC1 — Upgrade Policy

## Freeze rule

During the competition window, do not casually upgrade any of the following:

- Agent Framework packages
- Foundry hosting packages
- `azure-ai-projects` or Azure SDK dependencies
- Terraform providers or `azd`
- model deployment/version
- Toolbox version
- Foundry IQ Knowledge Base/index
- ReasonFuse Run Contract

An exception requires all of the following:

1. A blocking defect is recorded.
2. The proposed change and scope are reviewed.
3. The exact versions/configuration are updated in the release manifest.
4. The affected local regression is rerun.
5. Any Hosted impact is explicitly revalidated when budget and authorization exist.

## Budget rule

- Default commands are local and do not provision Azure.
- The competition benchmark remains `15 scenarios × 1 run`.
- The four signature demos use three local repetitions after reset.
- Hosted deployment is opt-in and must be explicitly authorized.

## Source of truth

The frozen values are recorded in:

- `config/release/competition_rc1.yaml`
- `docs/phases/phase-05-pre-competition-freeze/release-manifest.json`
- `pyproject.toml`
- `uv.lock`
- `requirements.txt`
- `infra/.terraform.lock.hcl`
