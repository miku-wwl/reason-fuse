param(
    [ValidateSet('local', 'hosted-check')]
    [string]$Mode = 'local'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

switch ($Mode) {
    'local' {
        & (Join-Path $root 'demo/reset.ps1')
        if (-not $?) { throw 'local reset failed' }
        & (Join-Path $root 'scripts/phase5_preflight.ps1')
        if (-not $?) { throw 'local preflight failed' }
        Write-Output 'EMERGENCY_RECOVERY=PASS (local fixture reset and preflight)'
    }
    'hosted-check' {
        Write-Output 'HOSTED_RECOVERY=CHECK_ONLY'
        Write-Output 'No APIM weights or Azure resources are modified by this command.'
        & (Join-Path $root 'scripts/phase5_preflight.ps1') -Hosted
        if (-not $?) { throw 'hosted check failed' }
        Write-Output 'EMERGENCY_RECOVERY=PASS (hosted check only)'
    }
}
