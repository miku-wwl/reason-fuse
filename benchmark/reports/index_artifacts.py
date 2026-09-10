"""Create a SHA-256 index for one Phase 3 evidence batch."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def index(run_dir: str | Path) -> Path:
    run = Path(run_dir)
    artifacts = []
    for path in sorted(run.rglob("*")):
        if not path.is_file() or path.name == "index.json":
            continue
        artifacts.append({"path": path.relative_to(run).as_posix(), "bytes": path.stat().st_size, "sha256": _sha256(path), "status": "PRESENT"})
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    payload = {
        "phase": "Phase 3 Evidence Benchmark Construction",
        "result": "PHASE3_CONSTRUCTION_EVIDENCE_INDEXED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "batch": run.name,
        "manifest_sha256": _sha256(run / "manifest.json"),
        "artifacts": artifacts,
        "summary": {"expected_runs": manifest["expected_runs"], "actual_runs": manifest["actual_runs"], "valid_runs": manifest["valid_runs"], "invalid_runs": manifest["invalid_runs"]},
        "scope": manifest["scope"],
    }
    destination = run / "index.json"
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PHASE3_EVIDENCE_INDEXED artifacts={len(artifacts)} path={destination}")
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    index(args.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
