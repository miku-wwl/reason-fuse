param(
    [switch]$DeployHosted
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv is required for the frozen local build'
}

Write-Output 'CLEAN_BUILD_MODE=LOCAL_SAFE'
uv sync --frozen --python 3.13
if ($LASTEXITCODE -ne 0) { throw "uv sync failed: $LASTEXITCODE" }

terraform -chdir=infra init -backend=false -input=false
if ($LASTEXITCODE -ne 0) { throw "terraform init failed: $LASTEXITCODE" }
terraform -chdir=infra validate
if ($LASTEXITCODE -ne 0) { throw "terraform validate failed: $LASTEXITCODE" }

& (Join-Path $root 'scripts/phase5_preflight.ps1')
if ($LASTEXITCODE -ne 0) { throw "Phase 5 preflight failed: $LASTEXITCODE" }

if (-not $DeployHosted) {
    Write-Output 'HOSTED_DEPLOY=NOT REQUESTED'
    Write-Output 'CLEAN_BUILD=PASS (local-safe; Azure unchanged)'
    exit 0
}

if ($env:PHASE5_ALLOW_HOSTED_DEPLOY -ne 'I_UNDERSTAND_AZURE_COST') {
    throw 'Hosted deployment is fail-closed. Set PHASE5_ALLOW_HOSTED_DEPLOY=I_UNDERSTAND_AZURE_COST and rerun with -DeployHosted.'
}

Write-Output 'HOSTED_DEPLOY=EXPLICITLY_AUTHORIZED'
terraform -chdir=infra apply -input=false -auto-approve
if ($LASTEXITCODE -ne 0) { throw "terraform apply failed: $LASTEXITCODE" }
azd provision --no-prompt
if ($LASTEXITCODE -ne 0) { throw "azd provision failed: $LASTEXITCODE" }
azd deploy --no-prompt
if ($LASTEXITCODE -ne 0) { throw "azd deploy failed: $LASTEXITCODE" }
& (Join-Path $root 'scripts/phase5_preflight.ps1') -Hosted
if ($LASTEXITCODE -ne 0) { throw "Hosted post-deploy preflight failed: $LASTEXITCODE" }
Write-Output 'CLEAN_BUILD=PASS (hosted; explicitly authorized)'
