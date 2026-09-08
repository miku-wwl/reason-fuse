$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
foreach ($script in Get-ChildItem -LiteralPath scripts -Filter '*.ps1' -File) {
    $parseTokens = $null
    $parseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($script.FullName, [ref]$parseTokens, [ref]$parseErrors)
    if ($parseErrors.Count) { throw "PowerShell parse failed: $($script.Name): $parseErrors" }
}
Write-Output 'POWERSHELL_PARSE_PASS'
.venv/Scripts/python.exe -m compileall -q src scripts tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
.venv/Scripts/python.exe tests/local_wiring.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
.venv/Scripts/python.exe tests/local_history_audit.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv lock --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git diff --check
exit $LASTEXITCODE
