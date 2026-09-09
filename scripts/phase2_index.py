"""Index an explicit construction batch; no date-specific search for PASS."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/phase-02-core"
RUNS = ROOT / "evidence/phase-01-runtime-validation/runs"
REQUIRED = {"a-off", "b-on", "c-exact", "d-oscillation", "e-retrieval", "f-useful",
            "g-outcome-failure", "h-budget", "i-outcome-unknown", "j-database-recheck"}


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def artifact(path, layer):
    events = rows(path) if path.suffix == ".jsonl" else []
    results = [e for e in events if e.get("event") == "RESULT"]
    result = results[-1] if results else {}
    commands = [e["argv"] for e in events if e.get("event") in {"START", "COMMAND"} and e.get("argv")]
    recorded_at = events[0].get("timestamp_utc") if events else None
    timestamp_utc = datetime.fromisoformat(recorded_at).astimezone(timezone.utc).isoformat() if recorded_at else None
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "evidence_layer": layer, "status": result.get("status", "SUPPORTING_ARTIFACT"),
            "exit_code": result.get("exit_code"), "timestamp_utc": timestamp_utc,
            "commands": commands}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    batch = (EVIDENCE / args.batch).resolve()
    assert batch.parent == EVIDENCE.resolve(), "Batch must be a direct evidence subdirectory"
    identity = json.loads((ROOT / "src/reasonfuse/validation/build_identity.json").read_text())
    environment = json.loads((ROOT / "evidence/phase-01-runtime-validation/environment-current.json").read_text())
    scenarios = {}
    for path in sorted(batch.glob("*-hosted.jsonl")):
        events = rows(path)
        runtime = [e["state"]["reasonfuse_core"] for e in events if e.get("event") == "RUNTIME_STATE"]
        builds = [e["state"]["build_identity"] for e in events if e.get("event") == "RUNTIME_STATE"]
        for build in builds:
            assert build["source_manifest_sha256"] == identity["source_manifest_sha256"], "Mixed runtime identity"
        for event in events:
            if event.get("event") == "SCENARIO_RESULT":
                entry = {**artifact(path, "REAL_HOSTED_INTEGRATION"), "status": event["status"],
                         "contract": runtime[-1].get("contract_limits") if runtime else None,
                         "enabled": runtime[-1].get("reasonfuse_enabled") if runtime else None}
                scenarios.setdefault(event["scenario"], []).append(entry)
    assert set(scenarios) == REQUIRED, f"Missing scenarios: {REQUIRED - set(scenarios)}"
    assert all(attempts[-1]["status"] == "PASS" for attempts in scenarios.values()), "Required final scenario failed"
    assert scenarios["a-off"][-1]["contract"] == scenarios["b-on"][-1]["contract"], "OFF/ON contracts differ"
    assert scenarios["a-off"][-1]["enabled"] is False and scenarios["b-on"][-1]["enabled"] is True
    recorders = sorted(RUNS.rglob(f"*-{args.batch}.jsonl"))
    assert recorders, "No command recorders for this batch"
    cutoff = recorders[0].name.split("-", 1)[0]
    dependencies = [p for p in sorted(RUNS.rglob("*.jsonl")) if p.name.split("-", 1)[0] >= cutoff]
    compatibility = [p for p in dependencies if p.name.endswith(f"batch-{args.batch}-compatibility.jsonl")]
    resets = [p for p in dependencies if p.name.endswith("-reset.jsonl")]
    environments = [p for p in dependencies if p.name.endswith("-environment.jsonl")]
    assert compatibility and artifact(compatibility[-1], "")['status'] == "PASS"
    assert resets and artifact(resets[-1], "")['status'] == "RESET_COMPLETE"
    assert environments and artifact(environments[-1], "")['status'] == "PASS"
    for agent in environment["agents"]:
        assert agent["env"]["REASONFUSE_ENABLED"] == "true"
        assert json.loads(agent["env"]["REASONFUSE_CONTRACT_JSON"]) == {}, "Final deployment must use defaults"
    local = []
    for suffix, layer in [("local-core", "LOCAL_CORE"), ("operations-api", "LOCAL_INTEGRATION")]:
        paths = sorted(EVIDENCE.glob(f"local-*/*-{suffix}.jsonl"))
        assert paths and artifact(paths[-1], layer)["status"] == "PASS"
        local.append(artifact(paths[-1], layer))
    units = sorted(RUNS.rglob(f"*-{args.batch}-unit.jsonl"))
    assert units and artifact(units[-1], "LOCAL_UNIT")["status"] == "PASS"
    local.append(artifact(units[-1], "LOCAL_UNIT"))
    packages = [(p, e) for p in dependencies for e in rows(p)
                if e.get("event") == "PACKAGE_MANIFEST" and e["build"] == identity]
    assert packages, "Missing audited native package"
    manifest_path, package = packages[-1]
    assert all(a["code_configuration"]["content_hash"] == package["sha256"] for a in environment["agents"])
    source_dir = batch / "sources"
    source_dir.mkdir(exist_ok=True)
    package_copy = source_dir / "hosted-code.zip"
    shutil.copyfile(package["package"], package_copy)
    assert hashlib.sha256(package_copy.read_bytes()).hexdigest() == package["sha256"]
    index = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "phase": "phase-02-core", "batch": args.batch,
        "result": "CONSTRUCTION_COMPLETE_READY_FOR_INDEPENDENT_VALIDATION",
        "source_identity": identity, "deployed_agents": environment["agents"],
        "hosted_scenarios": scenarios, "local_evidence": local,
        "compatibility_regression": artifact(compatibility[-1], "REAL_HOSTED_REGRESSION"),
        "reset": artifact(resets[-1], "REAL_HOSTED_RESET"),
        "environment": artifact(environments[-1], "DEPLOYED_ENVIRONMENT"),
        "audited_package": artifact(package_copy, "AUDITED_PACKAGE"),
        "package_manifest": artifact(manifest_path, "PACKAGE_MANIFEST"),
        "supporting_evidence": [artifact(p, "COMMAND_OR_DEPLOYMENT_EVIDENCE") for p in dependencies],
        "boundaries": {"foundry_iq": "NOT VERIFIED; deterministic retrieval fixture",
                       "production_restart": "NOT VERIFIED; simulated Operations API",
                       "independent_phase2_validation": "NOT RUN"},
    }
    content = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    (batch / "index.json").write_text(content, encoding="utf-8")
    (EVIDENCE / "index.json").write_text(content, encoding="utf-8")
    print(f"PHASE2_INDEX_VERIFIED {batch / 'index.json'}")


if __name__ == "__main__":
    main()
