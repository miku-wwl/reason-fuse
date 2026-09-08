"""Read-only second-pass evidence checks; not a substitute for live tests."""
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import Evidence


def read_events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def review(evidence):
    index_path = ROOT / "evidence/phase-01-runtime-validation/verification-20260907T232624Z/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["status"] == "PASS", "Final index has not passed its two-batch gates"
    artifacts = index["files"] + index["source_snapshot"] + index["audited_packages"] + index["reports"]
    secrets = [value.encode() for name, value in os.environ.items() if len(value) > 8 and
               any(part in name.upper() for part in ["_KEY", "CONNECTION_STRING", "PASSWORD", "SECRET", "TOKEN"])]
    for artifact in artifacts:
        path = ROOT / artifact["path"]
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == artifact["sha256"], f"Hash mismatch: {artifact['path']}"
        assert not any(secret in data for secret in secrets), f"Sensitive value found in {artifact['path']}"
        assert not re.search(rb"Bearer\s+[A-Za-z0-9_.-]{30,}", data), f"Raw bearer value in {artifact['path']}"
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    assert not name.startswith((".azure/", ".venv", ".tools/", ".env")), "Private upload member"
                    assert not any(secret in archive.read(name) for secret in secrets), "Sensitive upload member"
    for label, batch in index["batches"].items():
        requirements = batch["requirements"]
        def events(case):
            return read_events(ROOT / requirements[case][0]["path"])
        for case in ["spike02_toolbox_allow", "spike02_toolbox_block", "spike03_approval_approve", "spike03_approval_deny", "spike03_approval_binding"]:
            for record in requirements[case]:
                entries = read_events(ROOT / record["path"])
                intervals = [e["result"] for e in entries if e["event"] in {"COUNTER_RESET", "EXTERNAL_COUNTERS"}]
                assert intervals[0]["counts"] == {}, "Counter proof did not start at zero"
                assert len({e["epoch"] for e in intervals}) == 1, "Counter epoch invalidates evidence"
                responses = [e["body"] for e in entries if e["event"] == "RESPONSE" and e["body"].get("agent_session_id")]
                assert len({body["agent_session_id"] for body in responses}) == 1
                assert intervals[-1]["counts"] == ({"dns_resolution:api.reasonfuse.local": 1} if case == "spike02_toolbox_allow" else
                    {"restart_service:orders": 1} if case in {"spike03_approval_approve", "spike03_approval_binding"} else {})
        binding = events("spike03_approval_binding")
        approvals = [item for e in binding if e["event"] == "RESPONSE" for item in e["body"].get("output", []) if item["type"] == "mcp_approval_request"]
        assert len(approvals) == 2 and approvals[0]["id"] != approvals[1]["id"]
        assert [json.loads(item["arguments"]) for item in approvals] == [
            {"body": {"service_name": "orders"}}, {"body": {"service_name": "payments"}}]
        assert any(e["event"] == "SAME_ACTION_REPLAY" for e in binding)
        assert any(item.get("type") == "mcp_approval_response" and item.get("approval_request_id") == approvals[1]["id"] and item.get("approve") is False
                   for e in binding if e["event"] == "REQUEST" and isinstance(e["body"].get("input"), list) for item in e["body"]["input"])
        history = events("spike01_history_session")
        observations = [e for e in history if e["event"] == "HISTORY_AUDIT_ASSERTIONS"]
        assert len(observations) == 2
        sse = [e for e in events("spike04_sse") if e["event"] == "SSE_EVENT"]
        done = next(e["arrival_seconds"] for e in sse if e["body"]["type"] == "response.completed")
        deltas = [e["arrival_seconds"] for e in sse if e["body"]["type"] == "response.output_text.delta"]
        assert len(deltas) == 4 and all(arrival < done for arrival in deltas)
        assert all(deltas[i + 1] - deltas[i] >= .35 for i in range(3)) and deltas[-1] - deltas[0] >= 1.5
        assert not any(e["body"]["type"] in {"error", "response.failed"} for e in sse)
        cohort = events("spike04_new_session_control")
        policy = next(e for e in cohort if e["event"] == "COHORT_POLICY")
        assert policy["samples"] == 60 and policy["fresh_cookie_jar_per_sample"]
        requests = [e for e in cohort if e["event"] == "REQUEST"]
        assert len(requests) == 60 and all(e["cookie_names"] == [] for e in requests)
        routing = next(e for e in cohort if e["event"] == "ASSERTIONS")
        telemetry = next(e for e in events("metadata_telemetry") if e["event"] == "ASSERTIONS")
        deploy = next(e for e in events("environment") if e["event"] == "EXACT_DEPLOYED_PACKAGE")
        evidence.write("BATCH_REVIEW", batch=label, history=observations, approval_ids=[item["id"] for item in approvals],
                       routing=routing, sse_delta_arrivals=deltas, sse_completed_at=done,
                       telemetry=telemetry, deployment=deploy)
    markdowns = [ROOT / "ReasonFuse_Phase2_Core_Construction_Prompt.md",
                 ROOT / "docs/phases/phase-01-runtime-validation/verification-report.md",
                 ROOT / "docs/phases/phase-01-runtime-validation/verification-open-questions.md"]
    for path in markdowns:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("http:", "https:", "#")):
                continue
            assert (path.parent / target.split("#")[0].strip("<>")).exists(), f"Broken link in {path.name}: {target}"
    evidence.write("RESULT", status="PASS", exit_code=0, evidence_layer="evidence_consistency_review", checked_artifacts=len(artifacts))
    print(f"ARTIFACT_REVIEW_PASS {evidence.path}")


if __name__ == "__main__":
    evidence = Evidence("artifact-review")
    try:
        review(evidence)
    except Exception as error:
        evidence.write("RESULT", status="FAIL", exit_code=1, error_type=type(error).__name__, error=str(error))
        raise
