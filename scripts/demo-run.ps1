[CmdletBinding()]
param([Parameter(Mandatory)][string]$RunId, [Parameter(Mandatory)][ValidateSet('A','B','C')][string]$Story,
      [switch]$Execute, [switch]$DryRun)
$ErrorActionPreference = 'Stop'
if ($Execute -and $DryRun) { throw 'Choose Execute or DryRun, not both.' }
$python = Join-Path (Split-Path -Parent $PSScriptRoot) '.venv/Scripts/python.exe'
$arguments = @('-X', 'utf8', (Join-Path $PSScriptRoot 'demo_support.py'), 'run', '--run', $RunId, '--story', $Story)
if ($Execute) { $arguments += '--execute' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "Demo $Story failed ($LASTEXITCODE). Preserve evidence; do not retry for a better result." }
