[CmdletBinding()]
param([Parameter(Mandatory)][string]$RunId, [switch]$Execute, [switch]$DryRun)
$ErrorActionPreference = 'Stop'
if ($Execute -and $DryRun) { throw 'Choose Execute or DryRun, not both.' }
$python = Join-Path (Split-Path -Parent $PSScriptRoot) '.venv/Scripts/python.exe'
$arguments = @('-X', 'utf8', (Join-Path $PSScriptRoot 'demo_support.py'), 'down', '--run', $RunId)
if ($Execute) { $arguments += '--execute' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "demo-down failed ($LASTEXITCODE). Cleanup is NOT confirmed; retain the ownership manifest." }
