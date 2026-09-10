"""Generate the machine-readable Phase 5 competition release manifest.

The manifest records the frozen release contract and hashes the canonical
configuration/report inputs. It never reads secrets and never deploys Azure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "phases" / "phase-05-pre-competition-freeze" / "release-manifest.json"

FILES_TO_HASH = (
    "pyproject.toml",
    "uv.lock",
    "requirements.txt",
    "azure.yaml",
    "config/release/competition_rc1.yaml",
    "docs/phases/phase-03-evidence-benchmark/verification-report.md",
    "docs/phases/phase-04-production-story/PHASE4_REPORT.md",
    "docs/phases/phase-04-production-story/PHASE4_CLOUD_VERIFICATION_REPORT.md",
    "ReasonFuse_Phase5_PreCompetition_Freeze_Construction_Prompt.md",
)


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "NOT AVAILABLE"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_inventory() -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in FILES_TO_HASH:
        path = ROOT / relative
        result[relative] = _sha256(path) if path.exists() else "MISSING"
    return result


def build_manifest() -> dict[str, Any]:
    return {
        "release": {
            "name": "ReasonFuse Competition RC1",
            "phase": 5,
            "status": "CONSTRUCTION_READY",
            "architecture": "FROZEN",
            "proposed_tag": "reasonfuse-competition-rc1",
        },
        "source": {
            "git_commit": _git("rev-parse", "HEAD"),
            "working_tree_dirty": bool(_git("status", "--porcelain")),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "scope": {
            "benchmark_scenarios": 15,
            "benchmark_repetitions": 1,
            "signature_demo_repetitions": 3,
            "hosted_deployment_default": False,
            "hosted_evidence": "retained-phase4-report; live resources intentionally absent",
        },
        "runtime": {
            "model": "gpt-5-mini@2025-08-07",
            "prompt": "reasonfuse-phase4-prompt-v1",
            "toolbox": "reasonfuse-operations-v2",
            "knowledge_base": "reasonfuse-phase4-kb / reasonfuse-phase4-ks / reasonfuse-phase4-index",
            "reasonfuse_contract": "reasonfuse-contract-v1",
            "stable_agent": "reasonfuse-phase1-stable-v2",
            "candidate_agent": "reasonfuse-phase1-candidate-v2",
        },
        "dependencies": {
            "python": "3.13",
            "azd": "1.33.0",
            "terraform": "1.14.0",
            "azurerm": "5.4.0",
            "azapi": "2.12.0",
            "agent_framework_core": "1.17.0",
            "agent_framework_foundry_hosting": "1.0.0b260903",
            "azure_ai_projects": "2.3.0",
        },
        "freeze_policy": {
            "no_new_features": True,
            "no_new_architecture": True,
            "no_implicit_azure_deploy": True,
        },
        "canonical_file_sha256": _file_inventory(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_manifest(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PHASE5_RELEASE_MANIFEST_WRITTEN path={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
