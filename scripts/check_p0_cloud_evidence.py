"""Recheck this bounded cloud evidence package offline; performs no cloud calls."""

import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/evidence/p0-foundry"


def read(name):
    return json.loads((BASE / (name + ".json")).read_text(encoding="utf-8"))


def items(name):
    return read(name)["response"].get("output", [])


def text(name):
    return "".join(c.get("text", "") for i in items(name) if i.get("type") == "message"
                   for c in i.get("content", []))


def verdict(name):
    return json.loads(text(name))


def core(name):
    for item in items(name):
        if item.get("type") == "function_call_output":
            value = json.JSONDecoder().raw_decode(item["output"])[0]
            value = value.get("reasonfuse_core", value)
            if "core_state_version" in value:
                return value
    raise AssertionError("No observed core state in " + name)


def count(name, which="after"):
    state = read(name)["backend_" + which]
    return [state[k] for k in ("restart_count", "restart_attempt_count", "status_read_count")]


def automatic_verifier(name):
    return any(i.get("name", "").endswith("___service_status") and "-verify-" in i.get("call_id", "")
               for i in items(name))


def check():
    cases = []

    def record(number, condition, evidence, observation, candidate="NOT RERUN"):
        cases.append({"scenario": f"CLOUD-{number}", "v7": "PASS" if condition else "FAIL",
                      "v8": candidate, "evidence": evidence, "observation": observation})

    initial, continued, persisted = (core(n) for n in
        ("CLOUD-1-initial-retry", "CLOUD-1-continuation", "CLOUD-4-persisted"))
    v8persist = core("V8-CLOUD-1-persisted")
    record(1, initial["run_id"] == continued["run_id"] and persisted["side_effect_count"] == 1
           and persisted["tool_call_count"] == 3 and persisted["pending_postcondition"] is None,
           ["CLOUD-1-initial-retry", "CLOUD-1-continuation", "CLOUD-4-persisted", "V8-CLOUD-1-persisted"],
           "Sequential continuation preserves core identity, counts and resolved lifecycle.",
           "PASS" if v8persist["side_effect_count"] == 1 and v8persist["tool_call_count"] == 2
           and v8persist["action_lifecycle"]["status"] == "VERIFIED" else "FAIL")
    record(2, any(i["type"] == "mcp_approval_request" for i in items("CLOUD-2-request"))
           and count("CLOUD-2-request")[:2] == [0, 0], ["CLOUD-2-request", "V8-CLOUD-11-fork-request"],
           "Native approval request with zero independent dispatches/executions.",
           "PASS" if count("V8-CLOUD-11-fork-request")[:2] == [0, 0] else "FAIL")
    denied = core("CLOUD-3-continuation")
    record(3, verdict("CLOUD-3-denied")["outcome"] == "DENIED" and count("CLOUD-3-denied")[:2] == [0, 0]
           and denied["denied_proposal_count"] == 1 and denied["action_lifecycle"] is None
           and "UNSUPPORTED_CLOUD_SUCCESS" not in text("CLOUD-3-denied"),
           ["CLOUD-3-denied", "CLOUD-3-continuation"], "Denied proposal persists; no execution lifecycle is fabricated.")
    events = read("CLOUD-4-approved")["backend_after"]["events"]
    record(4, verdict("CLOUD-4-approved")["outcome"] == "OUTCOME_VERIFIED"
           and count("CLOUD-4-approved") == [1, 1, 1]
           and events[0]["result"]["generation"] == events[1]["result"]["generation"] == "g2"
           and events[1]["result"]["resource"] == "orders" and automatic_verifier("CLOUD-4-approved"),
           ["CLOUD-4-approved", "CLOUD-4-persisted", "V8-CLOUD-11-fork-approved-a"],
           "Accepted g2 followed by runtime-initiated registered HEALTHY/g2 verification.",
           "PASS" if verdict("V8-CLOUD-11-fork-approved-a")["outcome"] == "OUTCOME_VERIFIED"
           and count("V8-CLOUD-11-fork-approved-a") == [1, 1, 1] else "FAIL")
    stream = read("CLOUD-5-6-9-stream")
    deltas = [e for e in stream["events"] if e["data"].get("type") == "response.output_text.delta"]
    record(5, automatic_verifier("CLOUD-5-6-9-stream") and not stream["unsupported_claim_leaked"],
           ["CLOUD-5-request", "CLOUD-5-6-9-stream"], "Explicit skip/success instruction is replaced by runtime verification and outcome.")
    record(6, bool(deltas) and datetime.fromisoformat(deltas[0]["received_utc"]) >
           datetime.fromisoformat(stream["backend_after"]["events"][-1]["timestamp_utc"])
           and stream["first_text_backend"]["status_read_count"] == 1
           and "UNSUPPORTED_CLOUD_SUCCESS" not in "".join(e["data"].get("delta", "") for e in deltas),
           ["CLOUD-5-6-9-stream"], "First text delta arrives after verification; independent snapshot confirms status read already complete.")
    for number, status, outcome in [(7, "FAILED", "POSTCONDITION_FAILED"), (8, "UNKNOWN", "OUTCOME_UNKNOWN")]:
        result = verdict(f"CLOUD-{number}-approved")
        record(number, result["action_lifecycle"]["status"] == status and result["outcome"] == outcome
               and result["contained"] and count(f"CLOUD-{number}-replay-approved") == [1, 1, 1],
               [f"CLOUD-{number}-approved", f"CLOUD-{number}-replay-request", f"CLOUD-{number}-replay-approved"],
               f"{status} contains the lifecycle; newly approved replay makes no backend dispatch.")
    wrong, wrong8 = core("CLOUD-7-approved"), core("V8-CLOUD-11-fork-approved-a")
    record(9, wrong["pending_postcondition"] is not None and wrong["last_postcondition_result"] is None
           and wrong["action_lifecycle"]["status"] == "VERIFICATION_PENDING" and automatic_verifier("CLOUD-7-approved"),
           ["CLOUD-7-approved", "V8-CLOUD-11-fork-approved-a"],
           "Unrelated read_reasonfuse_state leaves the accepted obligation pending; only service_status resolves it.",
           "PASS" if wrong8["pending_postcondition"] is not None and automatic_verifier("V8-CLOUD-11-fork-approved-a") else "FAIL")
    record(10, all(verdict(f"CLOUD-{n}-replay-approved")["outcome"] == "BLOCKED"
            and count(f"CLOUD-{n}-replay-approved") == count(f"CLOUD-{n}-approved") for n in (7, 8)),
           ["CLOUD-7-replay-approved", "CLOUD-8-replay-approved"], "Native reapproval does not override containment.")
    pairs = {}
    for prefix in ("CLOUD-11-fork-approved", "CLOUD-11-explicit-approved", "V8-CLOUD-11-explicit-approved"):
        a, b = read(prefix + "-a"), read(prefix + "-b")
        assert a["response"]["agent_session_id"] == b["response"]["agent_session_id"]
        assert max(a["started_utc"], b["started_utc"]) < min(a["completed_utc"], b["completed_utc"])
        pairs[prefix] = {"same_platform_session": True, "overlap": True,
                         "backend_dispatches": max(count(prefix + "-a")[1], count(prefix + "-b")[1]),
                         "per_response_side_effect_counts": [verdict(prefix + x)["side_effect_count"] for x in ("-a", "-b")]}
    record(11, all(v["backend_dispatches"] <= 1 for k, v in pairs.items() if not k.startswith("V8")),
           [name + suffix for name in pairs for suffix in ("-a", "-b")] +
           ["V8-CLOUD-11-fork-approved-a", "V8-CLOUD-11-fork-approved-b", "V8-CLOUD-11-explicit-readback"],
           "FAIL: same-session requests obtain independent execution authority. Backend duplicate rejection masks a second possible mutation.",
           "FAIL" if pairs["V8-CLOUD-11-explicit-approved"]["backend_dispatches"] > 1 else "PASS")
    assert read("V8-CLOUD-11-fork-approved-b")["http_status"] == 409
    assert count("V8-CLOUD-11-fork-approved-a")[1] == 1
    toolset = {t["name"] for t in read("CLOUD-12-composed-inventory")["tools"]}
    record(12, toolset == {"reasonfuse-operations___operations___" + n for n in ("restart_service", "service_status")},
           ["CLOUD-12-fixture-inventory", "CLOUD-12-toolbox-inventory", "CLOUD-12-composed-inventory", "DEPLOY-source-verification"],
           "Two allowlisted external tools; no reset. Provider wiring is established from byte-matched source, not a remote all-tools enumeration.",
           "NOT RERUN")
    calls = [json.loads(p.read_text(encoding="utf-8")) for p in BASE.glob("*.json")]
    calls = [p for p in calls if "started_utc" in p and "request" in p]
    gate = "PASS" if all(c["v8"] == "PASS" for c in cases) else "FAIL"
    return {"gate": gate, "next": "ON/OFF EVALUATION" if gate == "PASS" else "FIX CLOUD BLOCKERS", "scenarios": cases,
            "concurrency": pairs, "hosted_response_requests": len(calls),
            "responses_with_model_usage": sum(bool(p.get("response", {}).get("usage")) for p in calls),
            "scope": "v7 complete gate; v8 partial candidate stopped after explicit-conversation concurrency failure",
            "local_regression": {"tests": 92, "exit_code": read("LOCAL-v8-regression")["exit_code"]}}


if __name__ == "__main__":
    report = check()
    (BASE / "scenario-index.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
