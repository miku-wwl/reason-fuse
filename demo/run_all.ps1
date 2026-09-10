param([int]$Repetitions = 3)
$ErrorActionPreference = "Stop"
& ".\demo\reset.ps1"
& ".\demo\preflight.ps1"
& ".venv/Scripts/python.exe" scripts/phase4_production_story.py --repetitions $Repetitions
if ($LASTEXITCODE -ne 0) { throw "Phase 4 production story failed" }
