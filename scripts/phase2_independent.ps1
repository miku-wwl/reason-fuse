param(
    [string]$Batch = ('verification-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$python = (Resolve-Path -LiteralPath '.venv/Scripts/python.exe').Path
$azd = (Resolve-Path -LiteralPath '.tools/azd-1.33.0/azd-windows-amd64.exe').Path
$env:PYTHONPATH = 'src'
$defaultContract = '{}'
$detectorContract = '{"max_stalled_steps":20,"required_objective_progress_interval":20}'
$restoreRequired = $false

function Checked([string]$Label, [string[]]$Command) {
    & $python scripts/verification_command.py ($Batch + '-' + $Label) -- @Command
    if ($LASTEXITCODE -ne 0) { throw "Independent validation command failed: $Label" }
}

function Configure([string]$Enabled, [string]$Contract) {
    & $azd env set REASONFUSE_PROFILE phase2
    if ($LASTEXITCODE -ne 0) { throw 'profile configuration failed' }
    & $azd env set REASONFUSE_ENABLED $Enabled
    if ($LASTEXITCODE -ne 0) { throw 'mode configuration failed' }
    & $azd env set REASONFUSE_CONTRACT_JSON $Contract
    if ($LASTEXITCODE -ne 0) { throw 'contract configuration failed' }
}

function DeployStable([string]$Label) {
    Checked $Label @($azd, 'deploy', 'stable', '--no-prompt')
}

function RunCase([string]$Label, [string]$Case, [int]$TurnDelay = 0) {
    $command = @($python, 'scripts/phase2_hosted.py', $Case, '--batch', $Batch)
    if ($TurnDelay -gt 0) { $command += @('--turn-delay', $TurnDelay.ToString()) }
    Checked $Label $command
}

try {
    # Supporting local evidence is collected in this independent batch.
    Checked '00-unit' @($python, '-m', 'unittest', 'discover', '-s', 'tests/unit', '-v')
    Checked '01-local-core' @($python, 'scripts/phase2_local.py')
    Checked '02-local-operations' @($python, 'scripts/phase2_operations_local.py')

    # A fresh audited source/package deployment is the independent runtime base.
    Configure 'true' $defaultContract
    Checked '03-deploy-initial' @('pwsh', '-File', 'scripts/deploy.ps1')
    $restoreRequired = $true
    Checked '04-preflight-initial' @('pwsh', '-File', 'scripts/preflight.ps1')
    Checked '05-capture-initial' @($python, 'scripts/capture_environment.py')
    Checked '06-reset-before-trials' @($python, 'scripts/reset.py')

    # OFF/ON use the same stable source, model, tools, prompts and default contract.
    Configure 'false' $defaultContract
    DeployStable '10-deploy-off'
    RunCase '11-a-off-01' 'a-off'
    Configure 'true' $defaultContract
    DeployStable '12-deploy-on'
    RunCase '13-b-on-01' 'b-on'

    # Detector-specific override isolates exact loop, oscillation and budget gates.
    Configure 'true' $detectorContract
    DeployStable '20-deploy-detectors'
    foreach ($trial in 1..3) { RunCase ("21-c-exact-0{0}" -f $trial) 'c-exact' }
    foreach ($trial in 1..3) { RunCase ("22-d-oscillation-0{0}" -f $trial) 'd-oscillation' }
    RunCase '23-h-budget-01' 'h-budget' 45

    # Default-ON detector/retrieval/outcome campaign.
    Configure 'true' $defaultContract
    DeployStable '30-deploy-default'
    foreach ($trial in 1..3) { RunCase ("31-e-retrieval-0{0}" -f $trial) 'e-retrieval' }
    foreach ($trial in 1..3) { RunCase ("32-f-useful-0{0}" -f $trial) 'f-useful' }
    RunCase '33-j-database-recheck-01' 'j-database-recheck'
    foreach ($trial in 1..3) { RunCase ("34-g-outcome-failure-0{0}" -f $trial) 'g-outcome-failure' }
    RunCase '35-i-outcome-unknown-01' 'i-outcome-unknown'

    # Clean-start revalidation: fresh audited deployment, preflight, core paths, reset.
    Configure 'true' $defaultContract
    Checked '40-deploy-clean-start' @('pwsh', '-File', 'scripts/deploy.ps1')
    Checked '41-preflight-clean-start' @('pwsh', '-File', 'scripts/preflight.ps1')
    Checked '42-capture-clean-start' @($python, 'scripts/capture_environment.py')
    Checked '43-reset-clean-start' @($python, 'scripts/reset.py')
    Configure 'false' $defaultContract
    DeployStable '44-deploy-clean-off'
    RunCase '45-a-off-clean-start' 'a-off'
    Configure 'true' $defaultContract
    DeployStable '46-deploy-clean-on'
    RunCase '47-b-on-clean-start' 'b-on'
    RunCase '48-f-useful-clean-start' 'f-useful'
    RunCase '49-g-outcome-failure-clean-start' 'g-outcome-failure'
    RunCase '50-i-outcome-unknown-clean-start' 'i-outcome-unknown'

    Configure 'true' $defaultContract
    DeployStable '51-deploy-final-default'
    Checked '52-capture-final' @($python, 'scripts/capture_environment.py')
    Checked '53-reset-final' @($python, 'scripts/reset.py')
    Write-Output "PHASE2_INDEPENDENT_BATCH_PASS $Batch"
}
finally {
    if ($restoreRequired) {
        try {
            Configure 'true' $defaultContract
            & $azd deploy stable --no-prompt | Out-Host
        }
        catch {
            Write-Error "Failed to restore default ON in finally: $($_.Exception.Message)"
        }
    }
}
