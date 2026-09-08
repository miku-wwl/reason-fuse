# Run only after a complete corrected-initial batch has passed.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
Set-Location -LiteralPath $root
function Invoke-Checked([scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Clean-start command failed: $LASTEXITCODE" }
}
$initialBatch = Get-ChildItem -LiteralPath 'evidence/phase-01-runtime-validation/runs' -Recurse -File -Filter '*-batch-corrected-initial.jsonl' |
    Sort-Object Name | Select-Object -Last 1
if (-not $initialBatch) { throw 'No corrected initial batch found.' }
$initialResult = Get-Content -LiteralPath $initialBatch.FullName -Tail 1 | ConvertFrom-Json
if ($initialResult.event -ne 'RESULT' -or $initialResult.status -ne 'PASS') { throw 'Initial batch has not passed.' }
Write-Output "INITIAL_BATCH_PASS $($initialBatch.FullName)"
Invoke-Checked { pwsh -File scripts/reset.ps1 }
$venvPath = (Resolve-Path -LiteralPath (Join-Path $root '.venv')).Path
$toolsPath = (Resolve-Path -LiteralPath (Join-Path $root '.tools')).Path
$backupPath = [IO.Path]::GetFullPath((Join-Path $toolsPath ('clean-start-backup-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))))
if ($venvPath -ne (Join-Path $root '.venv')) { throw 'Unexpected virtual environment target.' }
if (-not $backupPath.StartsWith($toolsPath + [IO.Path]::DirectorySeparatorChar)) { throw 'Backup target escapes .tools.' }
if (Test-Path -LiteralPath $backupPath) { throw 'Backup target already exists.' }
Write-Output "PRESERVE_VENV source=$venvPath destination=$backupPath"
Move-Item -LiteralPath $venvPath -Destination $backupPath
if (Test-Path -LiteralPath $venvPath) { throw 'Fresh .venv path is not empty.' }
Invoke-Checked { uv sync --frozen --python 3.13 }
Invoke-Checked { pwsh -File scripts/bootstrap.ps1 }
Invoke-Checked { pwsh -File scripts/deploy.ps1 }
Invoke-Checked { .venv/Scripts/python.exe scripts/verification_batch.py clean-start }
Invoke-Checked { pwsh -File scripts/reset.ps1 }
Write-Output 'CLEAN_START_COMPLETE'
