"""Index retained acceptance evidence and a nonsecret working-source snapshot."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import EVIDENCE_ROOT, now


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    destination = EVIDENCE_ROOT / "verification-20260907T232624Z"
    destination.mkdir(exist_ok=True)
    records = []
    events_by_path = {}
    for path in sorted((EVIDENCE_ROOT / "runs").rglob("*.jsonl")):
        if path.name < "20260907T233918811421Z":
            continue
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        events_by_path[path] = events
        result = next((entry for entry in reversed(events) if entry["event"] == "RESULT"), {})
        records.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
                        "case": events[0].get("case"), "started_utc": events[0]["timestamp_utc"],
                        "result": result.get("status", "INCOMPLETE_CAPTURE"), "exit_code": result.get("exit_code")})
    batches = {}
    for label in ["corrected-initial", "clean-start"]:
        matching = [(p, e) for p, e in events_by_path.items() if p.name.endswith(f"-batch-{label}.jsonl")]
        if not matching:
            batches[label] = {"status": "NOT VERIFIED"}
            continue
        path, entries = matching[-1]
        result = entries[-1]
        batch_records = [record for record in records if entries[0]["timestamp_utc"] <= record["started_utc"] <= result["timestamp_utc"]]
        requirements = {}
        for case in ["preflight", "environment", "spike01_history_session", "spike02_toolbox_allow", "spike02_toolbox_block",
                     "spike03_approval_approve", "spike03_approval_deny", "spike03_approval_binding",
                     "spike04_affinity", "spike04_new_session_control", "spike04_sse", "metadata_telemetry"]:
            requirements[case] = [r for r in batch_records if r["case"] == case]
        batches[label] = {"status": result.get("status", "NOT VERIFIED"), "batch_evidence": path.relative_to(ROOT).as_posix(),
                          "requirements": requirements}
        if args.final:
            assert result.get("status") == "PASS", f"{label} did not pass"
            for case, cases in requirements.items():
                expected = 2 if case in {"spike02_toolbox_allow", "spike02_toolbox_block"} else 1
                assert len(cases) == expected and all(r["result"] == "PASS" for r in cases), (label, case, cases)
    if args.final:
        assert all(batch["status"] == "PASS" for batch in batches.values())
        clean_commands = [r for r in records if r["case"] == "clean-start-orchestration"]
        assert clean_commands and clean_commands[-1]["result"] == "PASS"
        resets = [r for r in records if r["case"] == "reset"]
        assert len(resets) >= 2 and resets[-1]["result"] == "RESET_COMPLETE"
    files = [ROOT / p for p in [".agentignore", "azure.yaml", "pyproject.toml", "uv.lock", "requirements.txt",
                               "infra/.terraform.lock.hcl", "ReasonFuse_Phase2_Core_Construction_Prompt.md"]]
    files += [p for folder in ["src", "scripts", "tests"] for p in (ROOT / folder).rglob("*")
              if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".ps1", ".sh", ".json", ".yaml"}]
    snapshots = []
    packages = {}
    for events in events_by_path.values():
        for entry in events:
            if entry["event"] != "PACKAGE_MANIFEST":
                continue
            target = destination / "packages" / (entry["sha256"] + ".zip")
            target.parent.mkdir(exist_ok=True)
            package = target if target.exists() else Path(entry["package"])
            assert sha(package) == entry["sha256"]
            if package != target:
                shutil.copyfile(package, target)
            packages[entry["sha256"]] = {"path": target.relative_to(ROOT).as_posix(), "sha256": sha(target),
                                         "source_manifest_sha256": entry["build"]["source_manifest_sha256"]}
    for path in files:
        relative = path.relative_to(ROOT)
        target = destination / "sources" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        snapshots.append({"source": relative.as_posix(), "path": target.relative_to(ROOT).as_posix(), "sha256": sha(target)})
    result = {"updated_utc": now(), "status": "PASS" if args.final else "IN_PROGRESS",
              "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "source_identity": json.loads((ROOT / "src/reasonfuse/validation/build_identity.json").read_text()),
              "batches": batches, "files": records, "source_snapshot": snapshots, "audited_packages": list(packages.values()),
              "clean_start_workflow": [r for r in records if r["case"] in {"clean-start-orchestration", "reset"}],
              "reports": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in
                          sorted((ROOT / "docs/phases/phase-01-runtime-validation").glob("verification-*.md"))],
              "retention": "User-authorized learning cleanup on 2026-09-08: superseded construction/diagnostic artifacts removed; complete accepted initial and clean-start batches retained. This is not a complete execution-history archive.",
              "source_snapshot_scope": "Working-source snapshot at index update; the audited ZIP and embedded build identity identify the runtime actually tested.",
              "scope": "bounded independent Phase 1 acceptance; deterministic external operations and middleware SSE"}
    (destination / "index.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"VERIFICATION_INDEX {destination / 'index.json'} files={len(records)} status={result['status']}")


if __name__ == "__main__":
    main()
