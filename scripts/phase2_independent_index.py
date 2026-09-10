"""Index and verify one independent Phase 2 repeat/clean-start campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "phase-02-core"
RUNS = ROOT / "evidence" / "phase-01-runtime-validation" / "runs"

EXPECTED_COUNTS = {
    "a-off": 2, "b-on": 2, "c-exact": 3, "d-oscillation": 3,
    "e-retrieval": 3, "f-useful": 4, "g-outcome-failure": 4,
    "h-budget": 1, "i-outcome-unknown": 2, "j-database-recheck": 1,
}


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path: Path, layer: str) -> dict:
    # The audited deployment package is a binary ZIP, not a JSONL recorder.
    # Keep the same artifact shape while avoiding a text decode for binaries.
    events = rows(path) if path.suffix.lower() == ".jsonl" else []
    result = [item for item in events if item.get("event") == "RESULT"]
    status = result[-1].get("status") if result else "SUPPORTING_ARTIFACT"
    timestamp = events[0].get("timestamp_utc") if events else None
    return {
        "path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path),
        "evidence_layer": layer, "status": status,
        "exit_code": result[-1].get("exit_code") if result else None,
        "timestamp_utc": timestamp,
        "commands": [item.get("argv") for item in events
                      if item.get("event") in {"START", "COMMAND"} and item.get("argv")],
    }


def output_paths(recorders: list[Path], marker: str) -> list[Path]:
    found = []
    for recorder in recorders:
        for event in rows(recorder):
            text = event.get("text", "") if event.get("event") == "OUTPUT" else ""
            if text.startswith(marker + " "):
                candidate = Path(text[len(marker) + 1:].strip())
                if candidate.exists():
                    found.append(candidate)
    return found


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    batch = (EVIDENCE / args.batch).resolve()
    assert batch.parent == EVIDENCE.resolve(), "Independent batch must be direct evidence subdirectory"

    identity = json.loads((ROOT / "src/reasonfuse/validation/build_identity.json").read_text(encoding="utf-8"))
    environment = json.loads((ROOT / "evidence/phase-01-runtime-validation/environment-current.json").read_text(encoding="utf-8"))
    hosted = {}
    for path in sorted(batch.glob("*-hosted.jsonl")):
        events = rows(path)
        for event in events:
            if event.get("event") == "START":
                build = event.get("build_identity")
                assert build and build["source_manifest_sha256"] == identity["source_manifest_sha256"], "Mixed source manifest"
            if event.get("event") == "SCENARIO_RESULT":
                hosted.setdefault(event["scenario"], []).append({
                    **artifact(path, "REAL_HOSTED_INTEGRATION"),
                    "status": event["status"], "error": event.get("error"),
                })
    assert set(hosted) == set(EXPECTED_COUNTS), f"Missing scenarios: {set(EXPECTED_COUNTS) - set(hosted)}"
    for scenario, expected in EXPECTED_COUNTS.items():
        assert len(hosted[scenario]) == expected, f"{scenario}: expected {expected}, got {len(hosted[scenario])}"
        assert all(item["status"] == "PASS" for item in hosted[scenario]), f"{scenario} has failed attempt"

    required_recorders = sorted(RUNS.rglob(f"*-{args.batch}-*.jsonl"))
    assert required_recorders, "No independent command recorders found"
    compatibility = sorted(RUNS.rglob(f"*batch-{args.batch}-compatibility.jsonl"))
    assert compatibility, "Missing independent compatibility batch"
    compatibility_events = rows(compatibility[-1])
    assert compatibility_events[-1].get("status") == "PASS", "Compatibility gate did not pass"
    reset_candidates = output_paths(required_recorders, "RESET_COMPLETE")
    assert reset_candidates, "Missing independent RESET_COMPLETE"
    environments = output_paths(required_recorders, "ENVIRONMENT_CAPTURED")
    assert environments, "Missing independent environment evidence"

    for agent in environment["agents"]:
        assert agent["env"]["REASONFUSE_ENABLED"] == "true"
        assert json.loads(agent["env"]["REASONFUSE_CONTRACT_JSON"]) == {}
    assert all(agent["status"] == "active" for agent in environment["agents"])

    local = []
    for suffix, layer in [("local-core", "LOCAL_CORE"), ("operations-api", "LOCAL_INTEGRATION")]:
        paths = sorted(EVIDENCE.glob(f"local-*/*-{suffix}.jsonl"))
        assert paths
        local.append(artifact(paths[-1], layer))
        assert local[-1]["status"] == "PASS"
    units = sorted(RUNS.rglob(f"*-{args.batch}-00-unit*.jsonl"))
    unit_passes = [path for path in units if artifact(path, "LOCAL_UNIT")["status"] == "PASS"]
    assert unit_passes, "No passing independent unit evidence"
    local.append(artifact(unit_passes[-1], "LOCAL_UNIT"))

    all_recent_records = sorted(RUNS.rglob("*.jsonl"))
    package_entries = []
    for recorder in all_recent_records:
        for event in rows(recorder):
            if event.get("event") == "PACKAGE_MANIFEST" and event.get("build") == identity:
                package_entries.append((recorder, event))
    assert package_entries, "Missing audited package manifest for current identity"
    manifest_path, package = package_entries[-1]
    assert all(agent["code_configuration"]["content_hash"] == package["sha256"] for agent in environment["agents"])
    source_dir = batch / "sources"
    source_dir.mkdir(exist_ok=True)
    package_copy = source_dir / "hosted-code.zip"
    shutil.copyfile(package["package"], package_copy)
    assert sha256(package_copy) == package["sha256"]

    index = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "phase-02-core", "batch": args.batch,
        "result": "INDEPENDENT_PHASE2_VALIDATION_PASS",
        "trial_plan": EXPECTED_COUNTS,
        "source_identity": identity, "deployed_agents": environment["agents"],
        "hosted_scenarios": hosted, "local_evidence": local,
        "compatibility_regression": artifact(compatibility[-1], "REAL_HOSTED_REGRESSION"),
        "reset": artifact(reset_candidates[-1], "REAL_HOSTED_RESET"),
        "environment": artifact(environments[-1], "DEPLOYED_ENVIRONMENT"),
        "audited_package": artifact(package_copy, "AUDITED_PACKAGE"),
        "package_manifest": artifact(manifest_path, "PACKAGE_MANIFEST"),
        "supporting_evidence": [artifact(path, "COMMAND_OR_DEPLOYMENT_EVIDENCE") for path in required_recorders],
        "negative_controls": {
            "local_core": "PASS; Todo-only, new evidence, state/noise, malformed/unknown and middleware controls",
            "hosted_scope": "OFF/ON and repeated detector/outcome trials use independent counters and fresh conversations",
        },
        "boundaries": {
            "foundry_iq": "NOT VERIFIED; deterministic retrieval fixture",
            "production_restart": "NOT VERIFIED; deterministic Operations API",
            "cloud_core_trace_correlation": "NOT VERIFIED; local emission and runtime decision state only",
        },
    }
    content = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    (batch / "index.json").write_text(content, encoding="utf-8")
    (EVIDENCE / "independent-index.json").write_text(content, encoding="utf-8")
    print(f"PHASE2_INDEPENDENT_INDEX_VERIFIED {batch / 'index.json'}")


if __name__ == "__main__":
    main()
