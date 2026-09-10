param([int]$Repetitions = 3)
$ErrorActionPreference = "Stop"
& ".\demo\reset.ps1"
& ".\demo\preflight.ps1"
& ".venv/Scripts/python.exe" scripts/phase4_production_story.py --demo candidate_regression --repetitions $Repetitions --no-report
if ($LASTEXITCODE -ne 0) { throw "Phase 4 candidate-regression demo failed" }
Write-Output "PHASE4_CANDIDATE_REGRESSION_PASS"
