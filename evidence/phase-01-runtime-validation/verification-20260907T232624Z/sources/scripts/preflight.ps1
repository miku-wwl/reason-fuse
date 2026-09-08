$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$azd = Join-Path $root '.tools/azd-1.33.0/azd-windows-amd64.exe'
& $azd ai agent doctor --no-prompt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
.venv/Scripts/python.exe scripts/toolbox_smoke.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
.venv/Scripts/python.exe scripts/preflight.py
exit $LASTEXITCODE
