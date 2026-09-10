param([int]$Repetitions = 3)
$ErrorActionPreference = "Stop"
& ".\demo\reset.ps1"
& ".\demo\preflight.ps1"
& ".venv/Scripts/python.exe" scripts/phase4_production_story.py --demo off_on --repetitions $Repetitions --no-report
if ($LASTEXITCODE -ne 0) { throw "Phase 4 OFF/ON demo failed" }
Write-Output "PHASE4_OFF_ON_PASS"
