param([switch]$Hosted)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv/Scripts/python.exe'
$env:PYTHONPATH = Join-Path $root 'src'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing frozen Python environment: $python"
}

function Invoke-Required([string]$Label, [scriptblock]$Command) {
    Write-Output "PHASE5_PREFLIGHT_START=$Label"
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Phase 5 preflight failed: $Label (exit $LASTEXITCODE)" }
    Write-Output "PHASE5_PREFLIGHT_PASS=$Label"
}

Invoke-Required 'compile' { & $python -m compileall -q src scripts tests }
Invoke-Required 'unit-unittest' { & $python -m unittest discover -s tests/unit -p 'test_*.py' }
Invoke-Required 'dataset' { & $python -m benchmark.datasets.validate_dataset --dataset benchmark/datasets/reasonfuse_v2.jsonl }
Invoke-Required 'phase4-local-preflight' { & $python scripts/phase4_production_story.py --preflight-only }
Invoke-Required 'release-manifest-generator' { & $python scripts/write_phase5_release_manifest.py --output (Join-Path $root 'docs/phases/phase-05-pre-competition-freeze/release-manifest.json') }

if (Get-Command terraform -ErrorAction SilentlyContinue) {
    Invoke-Required 'terraform-fmt-check' { terraform -chdir=infra fmt -check -recursive }
    Invoke-Required 'terraform-validate' { terraform -chdir=infra validate }
    Invoke-Required 'terraform-plan-safe' { & (Join-Path $root 'scripts/terraform_plan_safe.ps1') }
} else {
    Write-Output 'TERRAFORM=NOT VERIFIED (terraform executable unavailable)'
}

if ($Hosted) {
    Write-Output 'HOSTED_PREFLIGHT=REQUESTED'
    & (Join-Path $root 'scripts/preflight.ps1')
    if ($LASTEXITCODE -ne 0) { throw "Hosted preflight failed (exit $LASTEXITCODE)" }
    Write-Output 'HOSTED_PREFLIGHT=PASS'
} else {
    Write-Output 'HOSTED_PREFLIGHT=NOT VERIFIED (Hosted mode not requested; no Azure deployment performed)'
}

Write-Output 'PHASE5_PREFLIGHT=PASS'
