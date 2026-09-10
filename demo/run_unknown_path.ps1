param([int]$Repetitions = 3)
$ErrorActionPreference = "Stop"
& ".\demo\reset.ps1"
& ".\demo\preflight.ps1"
& ".venv/Scripts/python.exe" scripts/phase4_production_story.py --demo unknown_path --repetitions $Repetitions --no-report
if ($LASTEXITCODE -ne 0) { throw "Phase 4 unknown-path demo failed" }
Write-Output "PHASE4_UNKNOWN_PATH_PASS"
