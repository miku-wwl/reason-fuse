[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunId,
    [switch]$Execute,
    [switch]$DryRun,
    [string]$Subscription,
    [string]$ProjectEndpoint,
    [string]$ResponsesEndpoint,
    [ValidatePattern('^[1-9][0-9]*$')][string]$AgentVersion = '10'
)
$ErrorActionPreference = 'Stop'
if ($Execute -and $DryRun) { throw 'Choose Execute or DryRun, not both.' }
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv/Scripts/python.exe'
$arguments = @('-X', 'utf8', (Join-Path $PSScriptRoot 'demo_support.py'), 'up', '--run', $RunId)
$arguments += @('--agent-version', $AgentVersion)
if ($Execute) { $arguments += '--execute' }
if ($Subscription) { $arguments += @('--subscription', $Subscription) }
if ($ProjectEndpoint) { $arguments += @('--project-endpoint', $ProjectEndpoint) }
if ($ResponsesEndpoint) { $arguments += @('--responses-endpoint', $ResponsesEndpoint) }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "demo-up failed ($LASTEXITCODE); use the owned manifest for cleanup." }
