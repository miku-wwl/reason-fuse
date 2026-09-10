param(
    [switch]$Hosted
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv/Scripts/python.exe'
$env:PYTHONPATH = Join-Path $root 'src'
$runDir = Join-Path ([IO.Path]::GetTempPath()) ("reasonfuse-phase5-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

function Invoke-Step([string]$Name, [scriptblock]$Command) {
    Write-Output "PHASE5_REGRESSION_START=$Name"
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Phase 5 regression failed: $Name (exit $LASTEXITCODE)" }
    Write-Output "PHASE5_REGRESSION_PASS=$Name"
}

try {
    # Phase 1 critical runtime smoke and Phase 2 core regression.
    Invoke-Step 'phase1-local-wiring' { & $python tests/local_wiring.py }
    Invoke-Step 'phase1-phase2-unit' { & $python -m unittest discover -s tests/unit -p 'test_*.py' }

    # Phase 3 bounded 15x1 integrity run. Raw output is temporary by design.
    Invoke-Step 'phase3-dataset-validation' { & $python -m benchmark.datasets.validate_dataset --dataset benchmark/datasets/reasonfuse_v2.jsonl }
    Invoke-Step 'phase3-15x1-suite' { & $python -m benchmark.runners.run_suite --dataset benchmark/datasets/reasonfuse_v2.jsonl --output-dir (Join-Path $runDir 'phase3') --repetitions 1 --include-impact }
    Invoke-Step 'phase3-microbenchmark' { & $python -m benchmark.microbenchmark.run_microbenchmark --output (Join-Path $runDir 'microbenchmark.json') }

    # Phase 4 local production-story regression. Hosted checks are opt-in.
    Invoke-Step 'phase4-local-preflight' { & $python scripts/phase4_production_story.py --preflight-only }
    Invoke-Step 'phase4-signatures-3x' { & $python scripts/phase4_production_story.py --no-report --repetitions 3 }

    if ($Hosted) {
        Invoke-Step 'phase4-hosted-preflight' { & (Join-Path $root 'scripts/preflight.ps1') }
        Write-Output 'PHASE4_HOSTED=REQUESTED (full hosted E2E remains a separately authorized operation)'
    } else {
        Write-Output 'PHASE4_HOSTED=NOT VERIFIED (Azure deployment not requested)'
    }

    Write-Output 'PHASE5_FULL_REGRESSION=PASS'
} finally {
    if (Test-Path -LiteralPath $runDir) {
        Remove-Item -LiteralPath $runDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
