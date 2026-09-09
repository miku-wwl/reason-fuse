"""Hash the independently produced Phase 3 verification artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--source-batch", default="evidence/phase-03-evidence-benchmark/verification-20260909T-v2-construction")
    args = parser.parse_args()
    directory = Path(args.directory)
    artifacts = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "index.json":
            artifacts.append({"path": path.relative_to(directory).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path), "status": "PRESENT"})
    payload = {
        "phase": "Phase 3 Evidence Benchmark Independent Verification",
        "result": "PHASE3_INDEPENDENT_EVIDENCE_INDEXED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "artifacts": artifacts,
        "source_batch": args.source_batch,
        "boundaries": {
            "toolcall_accuracy_300_execution": "PASS",
            "toolcall_accuracy_threshold_quality": "PARTIAL (159/300)",
            "foundry_iq_native_retrieval": "NOT VERIFIED",
            "production_operations_backend": "PASS",
            "cloud_core_trace_correlation": "PASS",
            "concurrent_forked_turns": "PASS",
            "fresh_client_recovery_proxy": "PASS",
            "cold_start_recovery": "NOT VERIFIED",
        },
    }
    destination = directory / "index.json"
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PHASE3_INDEPENDENT_EVIDENCE_INDEXED artifacts={len(artifacts)} path={destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
