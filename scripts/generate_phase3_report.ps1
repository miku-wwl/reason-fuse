[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunDirectory
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$env:PYTHONPATH = "src"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Batch = Split-Path -Leaf $RunDirectory
$CommandEvidenceDir = Join-Path $RepoRoot "evidence\phase-03-evidence-benchmark\commands\$Batch"
New-Item -ItemType Directory -Force -Path $CommandEvidenceDir | Out-Null
$env:REASONFUSE_EVIDENCE_ROOT = $CommandEvidenceDir
& $Python scripts/verification_command.py ("phase3-$Batch-report") -- $Python -m benchmark.reports.generate_report --run-dir $RunDirectory
if ($LASTEXITCODE -ne 0) { throw "Phase 3 report generation failed" }
& $Python scripts/verification_command.py ("phase3-$Batch-index") -- $Python -m benchmark.reports.index_artifacts --run-dir $RunDirectory
if ($LASTEXITCODE -ne 0) { throw "Phase 3 evidence indexing failed" }
Write-Output "PHASE3_REPORT_AND_INDEX_COMPLETE run_dir=$RunDirectory"
