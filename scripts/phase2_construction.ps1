param([string]$Batch = ('construction-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')),
      [switch]$ResumeBudget)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$azd = (Resolve-Path -LiteralPath '.tools/azd-1.33.0/azd-windows-amd64.exe').Path
$python = (Resolve-Path -LiteralPath '.venv/Scripts/python.exe').Path
function Checked([string[]]$Command) {
    & $python scripts/verification_command.py $Batch -- @Command
    if ($LASTEXITCODE -ne 0) { throw "Construction command failed: $($Command -join ' ')" }
}
function Configure([string]$Enabled, [string]$Contract) {
    & $azd env set REASONFUSE_PROFILE phase2
    if ($LASTEXITCODE -ne 0) { throw 'profile configuration failed' }
    & $azd env set REASONFUSE_ENABLED $Enabled
    if ($LASTEXITCODE -ne 0) { throw 'mode configuration failed' }
    & $azd env set REASONFUSE_CONTRACT_JSON $Contract
    if ($LASTEXITCODE -ne 0) { throw 'contract configuration failed' }
}
function Cases([string[]]$Names) {
    foreach ($case in $Names) {
        $caseCommand = @($python, 'scripts/phase2_hosted.py', $case, '--batch', $Batch)
        if ($case -eq 'h-budget') { $caseCommand += @('--turn-delay', '45') }
        Checked $caseCommand
    }
}
$defaultContract = '{}'
$detectorContract = '{"max_stalled_steps":20,"required_objective_progress_interval":20}'
$restoreRequired = $false
try {
    if (-not $ResumeBudget) {
        Configure 'true' $defaultContract
        Checked @('pwsh', '-File', 'scripts/deploy.ps1')
        Cases @('b-on', 'e-retrieval', 'f-useful', 'g-outcome-failure', 'i-outcome-unknown', 'j-database-recheck')
        $restoreRequired = $true
        Configure 'false' $defaultContract
        Checked @($azd, 'deploy', 'stable', '--no-prompt')
        Cases @('a-off')
    }
    $restoreRequired = $true
    Configure 'true' $detectorContract
    Checked @($azd, 'deploy', 'stable', '--no-prompt')
    if (-not $ResumeBudget) { Cases @('c-exact', 'd-oscillation') }
    Cases @('h-budget')
} finally {
    if ($restoreRequired) {
        Configure 'true' $defaultContract
        Checked @($azd, 'deploy', 'stable', '--no-prompt')
    }
}
Checked @($python, 'scripts/capture_environment.py')
Checked @($python, 'scripts/verification_batch.py', ($Batch + '-compatibility'))
Checked @($python, 'scripts/reset.py')
Write-Output "PHASE2_CONSTRUCTION_BATCH_PASS $Batch"
