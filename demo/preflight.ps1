$ErrorActionPreference = "Stop"
& ".venv/Scripts/python.exe" scripts/phase4_production_story.py --preflight-only
if ($LASTEXITCODE -ne 0) { throw "Phase 4 local preflight failed" }
