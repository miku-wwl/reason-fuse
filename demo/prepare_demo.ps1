$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

& (Join-Path $root 'demo/reset.ps1')
if (-not $?) { throw 'reset failed' }
& (Join-Path $root 'scripts/phase5_preflight.ps1')
if (-not $?) { throw 'preflight failed' }

$python = Join-Path $root '.venv/Scripts/python.exe'
& $python scripts/phase4_production_story.py --no-report --repetitions 3
if ($LASTEXITCODE -ne 0) { throw "signature demo preparation failed: $LASTEXITCODE" }

Write-Output 'HOSTED_DEMO=NOT VERIFIED (no live Azure environment requested)'
Write-Output 'REASONFUSE DEMO READY'
