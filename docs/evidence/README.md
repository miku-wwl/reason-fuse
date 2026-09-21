# Evidence versions

Current commands are in the [repository README](../../README.md). Historical files
retain their original timestamps, outcomes and hashes; do not use old commands as
current operating instructions.

| Artifact | Historical scope |
| --- | --- |
| [cloud-e2e.md](cloud-e2e.md) | v6 proof; external store=false instructions superseded by v10 store=true |
| [validation-summary.md](validation-summary.md) | Early summary/counts; exactly-once wording does not establish a distributed guarantee |
| [foundry-local-e2e.json](foundry-local-e2e.json) | Earlier real local-model execution, not the final source |
| [p0-foundry-cloud-validation.md](p0-foundry-cloud-validation.md) | Preserved v7/v8 FAIL |
| [V9-native-identity.json](p0-foundry/hosted-concurrency/V9-native-identity.json) | Same-conversation diagnostic reproduction |
| [p0-hosted-concurrency-validation.md](p0-hosted-concurrency-validation.md) | Latest complete real Hosted gate: v10 CLOUD-1..12 PASS; fixture subsequently deleted |
| [scenario-index.json](p0-foundry/hosted-concurrency/scenario-index.json) | Per-case v10 raw artifact references |
| [source identity](p0-foundry/hosted-concurrency/V10-source-identity.json) | Deployed source, including historical README/.gitignore; support files compare to commit 389d1e1, core also compares to current source |
| [integrity manifest](p0-foundry/hosted-concurrency/evidence-manifest.json) | Immutable original v10 evidence and supporting files |

New submission artifacts live in `submission/`; local scripted results and cloud
results are distinct. See [final acceptance](../submission-sprint.md).
