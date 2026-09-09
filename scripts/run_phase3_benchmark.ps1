[CmdletBinding()]
param(
    [string]$Batch = "",
    [int]$Repetitions = 3,
    [switch]$IncludeImpact
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$env:PYTHONPATH = "src"
if ([string]::IsNullOrWhiteSpace($Batch)) {
    $Batch = "verification-$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))"
}
$RunDir = Join-Path $RepoRoot "evidence\phase-03-evidence-benchmark\$Batch"
$CommandEvidenceDir = Join-Path $RepoRoot "evidence\phase-03-evidence-benchmark\commands\$Batch"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Dataset = Join-Path $RepoRoot "benchmark\datasets\reasonfuse_v1.jsonl"
New-Item -ItemType Directory -Force -Path $RunDir, $CommandEvidenceDir | Out-Null
$env:REASONFUSE_EVIDENCE_ROOT = $CommandEvidenceDir

function Invoke-Checked([string]$Label, [string[]]$Command) {
    & $Python scripts/verification_command.py ("phase3-$Batch-$Label") -- @Command
    if ($LASTEXITCODE -ne 0) { throw "Phase 3 command failed: $Label" }
}

$Phase2Report = Join-Path $RepoRoot "docs\phases\phase-02-core\verification-report.md"
$Phase2Index = Join-Path $RepoRoot "evidence\phase-02-core\verification-20260909T110000Z\index.json"
if (-not (Test-Path -LiteralPath $Phase2Report) -or -not (Test-Path -LiteralPath $Phase2Index)) {
    throw "Phase 2 handoff artifacts are missing; refusing to construct Phase 3 evidence."
}
if (-not ((Get-Content -Raw -LiteralPath $Phase2Report) -match "INDEPENDENT_PHASE2_VALIDATION_PASS")) {
    throw "Phase 2 report does not contain the required independent PASS handoff."
}
$Phase2IndexBody = Get-Content -Raw -LiteralPath $Phase2Index | ConvertFrom-Json
if ($Phase2IndexBody.result -ne "INDEPENDENT_PHASE2_VALIDATION_PASS") {
    throw "Phase 2 evidence index is not an independent PASS handoff."
}

Invoke-Checked "dataset-generate" @($Python, "-m", "benchmark.datasets.generate_dataset")
Invoke-Checked "dataset-validate" @($Python, "-m", "benchmark.datasets.validate_dataset", "--dataset", $Dataset)
$args = @("-m", "benchmark.runners.run_suite", "--dataset", $Dataset, "--output-dir", $RunDir, "--repetitions", $Repetitions)
if ($IncludeImpact) { $args += "--include-impact" }
$suiteCommand = @($Python) + $args
Invoke-Checked "suite" $suiteCommand
Invoke-Checked "microbenchmark" @($Python, "-m", "benchmark.microbenchmark.run_microbenchmark", "--output", (Join-Path $RunDir "microbenchmark.json"))
Invoke-Checked "report" @($Python, "-m", "benchmark.reports.generate_report", "--run-dir", $RunDir)
Invoke-Checked "root-report" @($Python, "-m", "benchmark.reports.generate_report", "--run-dir", $RunDir, "--output", (Join-Path $RepoRoot "benchmark\PHASE3_REPORT.md"))
Invoke-Checked "index" @($Python, "-m", "benchmark.reports.index_artifacts", "--run-dir", $RunDir)
Write-Output "PHASE3_CONSTRUCTION_COMPLETE run_dir=$RunDir"
