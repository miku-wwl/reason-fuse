$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root

if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    throw 'terraform is required for the safe plan check'
}

$subscription = (az account show --query id -o tsv 2>$null).Trim()
if ([string]::IsNullOrWhiteSpace($subscription)) {
    # A syntactically valid placeholder is enough for refresh=false planning;
    # no Azure resource is contacted or created by this command.
    $subscription = '00000000-0000-0000-0000-000000000000'
}

terraform -chdir=infra plan `
    -refresh=false `
    -input=false `
    -lock=false `
    -no-color `
    -var="subscription_id=$subscription" `
    -var='location=australiaeast' `
    -var='resource_group_name=rg-reasonfuse-phase6-plan' `
    -var='environment_name=reasonfuse-phase6-plan' `
    -var='publisher_email=phase6-plan@example.invalid' `
    -var='operations_admin_key=phase6-local-plan-only'
if ($LASTEXITCODE -ne 0) { throw "terraform plan failed: $LASTEXITCODE" }

Write-Output 'TERRAFORM_PLAN_SAFE=PASS (refresh=false; no apply; no Azure resources changed)'
