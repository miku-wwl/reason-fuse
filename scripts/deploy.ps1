param([switch]$DnsOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$azd = Join-Path $root '.tools/azd-1.33.0/azd-windows-amd64.exe'
if (-not (Test-Path -LiteralPath $azd)) { & "$PSScriptRoot/bootstrap.ps1" }
function Invoke-Checked([scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" }
}
Invoke-Checked { uv sync --frozen --python 3.13 }
Invoke-Checked { uv export --frozen --no-dev --no-emit-project --no-hashes --output-file requirements.txt | Out-Null }
$subscription = az account show --query id -o tsv
if ($subscription -ne '7c73b89d-485e-43a9-8d66-b12b766d567f') { throw 'Login to the documented Azure for Students subscription first.' }
$settings = Join-Path $root '.azure/rf-phase1-aue/.env'
if (-not (Test-Path -LiteralPath $settings)) {
    Invoke-Checked { & $azd env new rf-phase1-aue --subscription $subscription --location australiaeast --no-prompt }
}
Invoke-Checked { & $azd env select rf-phase1-aue }
Invoke-Checked { & $azd env set AZURE_LOCATION australiaeast }
Invoke-Checked { & $azd env set AZURE_RESOURCE_GROUP rg-reasonfuse-phase1-aue }
Invoke-Checked { & $azd env set AZURE_AI_PROJECT_NAME reasonfuse-phase1 }
Invoke-Checked { & $azd env set AZD_RESOURCE_TOKEN_SALT phase1 }
$principal = az ad signed-in-user show --query id -o tsv
$publisher = az ad signed-in-user show --query userPrincipalName -o tsv
Invoke-Checked { & $azd env set AZURE_PRINCIPAL_ID $principal }
Invoke-Checked { & $azd env set PUBLISHER_EMAIL $publisher }
if (-not (Select-String -LiteralPath $settings -Pattern '^OPERATIONS_ADMIN_KEY=' -Quiet)) {
    $validationKey = [Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    Add-Content -LiteralPath $settings -Value ('OPERATIONS_ADMIN_KEY="' + $validationKey + '"')
}
Invoke-Checked { terraform -chdir=infra init -input=false }
Invoke-Checked { terraform -chdir=infra validate }
Invoke-Checked { & $azd provision --no-prompt }
$operationsApp = & $azd env get-value OPERATIONS_APP_NAME
Compress-Archive -LiteralPath 'tests/support/operations_api/server.py','tests/support/operations_api/dns_resolution.py','tests/support/operations_api/restart_service.py' -DestinationPath '.tools/operations-api.zip' -Force
Invoke-Checked { az webapp deploy --resource-group rg-reasonfuse-phase1-aue --name $operationsApp --src-path .tools/operations-api.zip --type zip --track-status false }
if ($DnsOnly) {
    Invoke-Checked { .venv/Scripts/python.exe scripts/create_toolbox.py }
} else {
    Invoke-Checked { .venv/Scripts/python.exe scripts/create_toolbox.py --include-restart }
}
Invoke-Checked { .venv/Scripts/python.exe scripts/toolbox_smoke.py }
Invoke-Checked { & $azd deploy --all --no-prompt }
foreach ($name in 'FOUNDRY_PROJECT_ENDPOINT','TOOLBOX_ENDPOINT','OPERATIONS_ENDPOINT','APIM_ENDPOINT') {
    $value = & $azd env get-value $name
    Write-Output "$name=$value"
}
