[CmdletBinding()]
param(
    [string]$RunDirectory = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$env:PYTHONPATH = "src"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if ([string]::IsNullOrWhiteSpace($RunDirectory)) {
    $RunDirectory = Join-Path $RepoRoot "evidence\phase-03-evidence-benchmark\microbenchmark-$(Get-Date -AsUTC -Format yyyyMMddTHHmmssZ)"
}
New-Item -ItemType Directory -Force -Path $RunDirectory | Out-Null
$Batch = Split-Path -Leaf $RunDirectory
$CommandEvidenceDir = Join-Path $RepoRoot "evidence\phase-03-evidence-benchmark\commands\$Batch"
New-Item -ItemType Directory -Force -Path $CommandEvidenceDir | Out-Null
$env:REASONFUSE_EVIDENCE_ROOT = $CommandEvidenceDir
& $Python scripts/verification_command.py ("phase3-$Batch-microbenchmark") -- $Python -m benchmark.microbenchmark.run_microbenchmark --output (Join-Path $RunDirectory "microbenchmark.json")
if ($LASTEXITCODE -ne 0) { throw "Phase 3 microbenchmark failed" }
