$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
foreach ($tool in 'az', 'uv', 'terraform') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Required command missing: $tool" }
}
$azd = Join-Path $root '.tools/azd-1.33.0/azd-windows-amd64.exe'
if (-not (Test-Path -LiteralPath $azd)) {
    New-Item -ItemType Directory -Force '.tools' | Out-Null
    Invoke-WebRequest 'https://github.com/Azure/azure-dev/releases/download/azure-dev-cli_1.33.0/azd-windows-amd64.zip' -OutFile '.tools/azd-1.33.0.zip'
    Expand-Archive -LiteralPath '.tools/azd-1.33.0.zip' -DestinationPath '.tools/azd-1.33.0'
}
foreach ($extension in @(
    @{Id='azure.ai.agents'; Version='1.0.0-beta.13'},
    @{Id='azure.ai.projects'; Version='1.0.0-beta.9'},
    @{Id='azure.ai.toolboxes'; Version='1.0.0-beta.6'}
)) {
    & $azd ext install $extension.Id --version $extension.Version --no-prompt
    if ($LASTEXITCODE -ne 0) { throw "Extension installation failed: $($extension.Id)" }
}
& $azd version
terraform version
uv --version
