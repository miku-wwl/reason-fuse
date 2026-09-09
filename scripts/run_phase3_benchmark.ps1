[CmdletBinding()]
param(
    [string]$Batch = "",
    [int]$Repetitions = 1,
    [switch]$IncludeImpact,
    [string]$DatasetPath = "benchmark\datasets\reasonfuse_v2.jsonl",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$env:PYTHONPATH = "src"
if ([string]::IsNullOrWhiteSpace($Batch)) {
    $Batch = "verification-$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))"
}
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path ([IO.Path]::GetTempPath()) "reasonfuse-phase3"
} elseif (-not [IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot = Join-Path $RepoRoot $OutputRoot
}
$RunDir = Join-Path $OutputRoot $Batch
$CommandEvidenceDir = Join-Path $OutputRoot "commands\$Batch"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Dataset = if ([IO.Path]::IsPathRooted($DatasetPath)) { $DatasetPath } else { Join-Path $RepoRoot $DatasetPath }
New-Item -ItemType Directory -Force -Path $RunDir, $CommandEvidenceDir | Out-Null
$env:REASONFUSE_EVIDENCE_ROOT = $CommandEvidenceDir

function Invoke-Checked([string]$Label, [string[]]$Command) {
    & $Python scripts/verification_command.py ("phase3-$Batch-$Label") -- @Command
    if ($LASTEXITCODE -ne 0) { throw "Phase 3 command failed: $Label" }
}

$Phase2Report = Join-Path $RepoRoot "docs\phases\phase-02-core\verification-report.md"
if (-not (Test-Path -LiteralPath $Phase2Report)) {
    throw "Phase 2 verification report is missing; refusing to construct Phase 3 evidence."
}
if (-not ((Get-Content -Raw -LiteralPath $Phase2Report) -match "INDEPENDENT_PHASE2_VALIDATION_PASS")) {
    throw "Phase 2 report does not contain the required independent PASS handoff."
}

Invoke-Checked "dataset-generate" @($Python, "-m", "benchmark.datasets.generate_dataset_v2", "--output", $Dataset)
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
