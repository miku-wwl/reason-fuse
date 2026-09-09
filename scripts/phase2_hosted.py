"""Execute Phase 2 core scenarios against the deployed Foundry Hosted Agent.

This is deliberately a real Responses/Toolbox driver. It does not label a
scenario PASS when the model stops voluntarily or when only a local engine
test was run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.support.validation import (  # noqa: E402
    HostedClient,
    Operations,
    approval_request,
    approval_response,
    output_text,
    runtime_state,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Phase2Evidence:
    def __init__(self, batch: str, turn_delay: float = 0):
        self.turn_delay = turn_delay
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.path = ROOT / "evidence" / "phase-02-core" / batch / f"{stamp}-hosted.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.write("START", batch=batch, evidence_layer="REAL_HOSTED_INTEGRATION", argv=sys.argv,
                   turn_delay_seconds=turn_delay,
                   build_identity=json.loads((ROOT / "src/reasonfuse/validation/build_identity.json").read_text()))

    def write(self, event: str, **fields):
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"timestamp_utc": utc_now(), "event": event, **fields},
                                    default=str) + "\n")


class Phase2Operations(Operations):
    def set_scenario(self, scenario: str):
        response = httpx.post(self.base + "/scenario", headers=self.headers,
                              json={"scenario": scenario}, timeout=90)
        response.raise_for_status()
        result = response.json()
        assert result["epoch"] == self.epoch, "Scenario change unexpectedly changed the epoch"
        self.evidence.write("SCENARIO_SET", scenario=scenario, epoch=result["epoch"])
        return result


def item_summaries(response: dict) -> list[dict]:
    summary = []
    for item in response.get("output", []):
        value = {"type": item.get("type"), "name": item.get("name"),
                 "call_id": item.get("call_id"), "id": item.get("id")}
        if item.get("type") in {"mcp_approval_request", "mcp_approval_response"}:
            value["approval_request_id"] = item.get("approval_request_id")
        summary.append(value)
    return summary


def tool_names(response: dict) -> list[str]:
    return [str(item.get("name")) for item in response.get("output", [])
            if item.get("type") in {"function_call", "mcp_call", "custom_tool_call"}
            and item.get("name")]


def has_tool(response: dict, name: str) -> bool:
    return name in tool_names(response)


def turn(evidence: Phase2Evidence, client: HostedClient, conversation: str,
         label: str, prompt_or_input):
    if evidence.turn_delay:
        evidence.write("HARNESS_PACING", label=label, seconds=evidence.turn_delay)
        time.sleep(evidence.turn_delay)
    response = client.turn(prompt_or_input, conversation=conversation)
    evidence.write("TURN", label=label, conversation_id=conversation,
                   response_id=response.get("id"),
                   agent_session_id=response.get("agent_session_id"),
                   output=item_summaries(response), tool_names=tool_names(response),
                   text_sha256=hashlib.sha256(output_text(response).encode()).hexdigest())
    return response


def state(evidence: Phase2Evidence, client: HostedClient, conversation: str, label: str) -> dict:
    response = turn(evidence, client, conversation, label, "Call read_runtime_state and return its exact JSON.")
    value = runtime_state(response)
    evidence.write("RUNTIME_STATE", label=label, conversation_id=conversation,
                   agent_session_id=response.get("agent_session_id"), state=value)
    return value


def core_state(value: dict) -> dict:
    core = value.get("reasonfuse_core")
    assert isinstance(core, dict), "Authoritative runtime state has no reasonfuse_core"
    return core


def new_case(evidence: Phase2Evidence, scenario: str, operations_scenario: str):
    external = Phase2Operations(evidence)
    external.reset()
    external.set_scenario(operations_scenario)
    client = HostedClient(evidence)
    conversation = client.conversation()
    evidence.write("SCENARIO_START", scenario=scenario, operations_scenario=operations_scenario,
                   conversation_id=conversation)
    return external, client, conversation


def close_case(external: Phase2Operations, client: HostedClient, scenario: str):
    try:
        external.snapshot()
    finally:
        client.close()
    external.evidence.write("SCENARIO_END", scenario=scenario)


def repeated_dns(evidence, client, conversation, hostname, count, label_prefix):
    responses = []
    for index in range(1, count + 1):
        prompt = (f"This is bounded detector turn {index}. Call operations___dns_resolution exactly once "
                  f"with hostname {hostname}. Do not summarize or stop the bounded scenario; "
                  "return only after submitting that exact tool call.")
        responses.append(turn(evidence, client, conversation, f"{label_prefix}-{index}", prompt))
    return responses


def scenario_a(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "A_off_no_progress", "no_progress_dns")
    try:
        responses = repeated_dns(evidence, client, conversation, "api.reasonfuse.local", 4, "off")
        counts = external.snapshot()["counts"]
        final = state(evidence, client, conversation, "off-final")
        core = core_state(final)
        assert not core["reasonfuse_enabled"], f"OFF run was enabled: {core}"
        assert not core["contained"], f"OFF run was contained: {core}"
        actual = counts.get("dns_resolution:api.reasonfuse.local", 0)
        assert actual >= 2, "OFF scenario stopped before demonstrating redundant behavior"
        evidence.write("ASSERTIONS", scenario="A_off_no_progress", mode="OFF",
                       harness_stop=True, voluntary_stop=actual < 4, tool_calls=actual,
                       fuse_reason=None, objective_progress=core.get("progress_history"),
                       run_id=core.get("run_id"), agent_session_id=final.get("agent_session_id"),
                       response_ids=[item.get("id") for item in responses])
    finally:
        close_case(external, client, "A_off_no_progress")


def scenario_b(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "B_on_no_progress", "no_progress_dns")
    try:
        responses = repeated_dns(evidence, client, conversation, "api.reasonfuse.local", 4, "on")
        blocked = responses[-1]
        counts = external.snapshot()["counts"]
        final = state(evidence, client, conversation, "on-final")
        core = core_state(final)
        assert core["reasonfuse_enabled"], f"ON run was disabled: {core}"
        assert core["contained"], f"ON run did not contain: {core}"
        assert core["fuse_reason"] == "NO_PROGRESS", core
        assert counts.get("dns_resolution:api.reasonfuse.local", 0) == 2, counts
        assert any(item.get("type") == "function_call_output" or item.get("type") == "custom_tool_call_output"
                   for item in blocked.get("output", [])), "No structured block result was returned"
        after = turn(evidence, client, conversation, "on-post-trip",
                     "Call operations___dns_resolution exactly once for api.reasonfuse.local.")
        assert external.snapshot()["counts"] == counts, "A post-trip dispatch reached Operations"
        evidence.write("ASSERTIONS", scenario="B_on_no_progress", mode="ON", harness_stop=False,
                       voluntary_stop=False, tool_calls=counts.get("dns_resolution:api.reasonfuse.local", 0),
                       fuse_reason=core["fuse_reason"], objective_progress=core.get("progress_history"),
                       detector_state=core, post_trip_output=item_summaries(after),
                       run_id=core.get("run_id"), agent_session_id=final.get("agent_session_id"))
    finally:
        close_case(external, client, "B_on_no_progress")


def scenario_c(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "C_exact_loop", "no_progress_dns")
    try:
        responses = repeated_dns(evidence, client, conversation, "api.reasonfuse.local", 3, "exact")
        final = state(evidence, client, conversation, "exact-final")
        core = core_state(final)
        assert core["contained"] and core["fuse_reason"] == "EXACT_LOOP", core
        assert external.snapshot()["counts"].get("dns_resolution:api.reasonfuse.local", 0) == 2
        evidence.write("ASSERTIONS", scenario="C_exact_loop", mode="ON", tool_sequence=tool_names(responses[0]) +
                       tool_names(responses[1]) + tool_names(responses[2]), fuse_reason=core["fuse_reason"],
                       detector_state=core, run_id=core.get("run_id"),
                       agent_session_id=final.get("agent_session_id"))
    finally:
        close_case(external, client, "C_exact_loop")


def scenario_d(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "D_oscillation", "no_progress_dns")
    try:
        responses = []
        for index, hostname in enumerate(["api.reasonfuse.local", "payments.reasonfuse.local",
                                          "api.reasonfuse.local", "payments.reasonfuse.local"], start=1):
            responses.append(turn(
                evidence, client, conversation, f"oscillation-{index}",
                f"Call operations___dns_resolution exactly once for hostname {hostname}. "
                "Continue this bounded period-2 detector scenario and do not summarize."))
        final = state(evidence, client, conversation, "oscillation-final")
        core = core_state(final)
        assert core["contained"] and core["fuse_reason"] == "OSCILLATING", core
        counts = external.snapshot()["counts"]
        assert sum(value for key, value in counts.items() if key.startswith("dns_resolution:")) == 3, counts
        evidence.write("ASSERTIONS", scenario="D_oscillation", mode="ON",
                       tool_sequence=[tool_names(item) for item in responses], fuse_reason=core["fuse_reason"],
                       detector_state=core, run_id=core.get("run_id"),
                       agent_session_id=final.get("agent_session_id"))
    finally:
        close_case(external, client, "D_oscillation")


def scenario_e(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "E_retrieval_churn", "retrieval_churn")
    try:
        responses = []
        for index, query in enumerate(["database failure", "db connectivity", "database issue"], start=1):
            responses.append(turn(
                evidence, client, conversation, f"retrieval-{index}",
                f"Call operations___retrieval_fixture exactly once with query {query}. "
                "This is the bounded deterministic retrieval fixture; keep executing the next query "
                "even when the effective evidence is unchanged."))
        final = state(evidence, client, conversation, "retrieval-final")
        core = core_state(final)
        assert core["contained"] and core["fuse_reason"] == "RETRIEVAL_CHURN", core
        counts = external.snapshot()["counts"]
        assert sum(value for key, value in counts.items() if key.startswith("retrieval_fixture:")) == 3, counts
        evidence.write("ASSERTIONS", scenario="E_retrieval_churn",
                       label="LIVE_HOSTED_WITH_DETERMINISTIC_RETRIEVAL_FIXTURE",
                       foundry_iq="NOT VERIFIED", mode="ON", tool_sequence=[tool_names(item) for item in responses],
                       fuse_reason=core["fuse_reason"], detector_state=core, run_id=core.get("run_id"),
                       agent_session_id=final.get("agent_session_id"))
    finally:
        close_case(external, client, "E_retrieval_churn")


def approved_restart(evidence, client, conversation, service="orders", verifier=None):
    requested = turn(evidence, client, conversation, "restart-request",
                     f"Call operations___restart_service exactly once with service_name {service}. "
                     "Submit the native tool call immediately for approval; do not ask for prose approval." +
                     (f" After acceptance verify only with operations___{verifier} for {service}." if verifier else ""))
    pending = approval_request(requested)
    approved = client.turn([approval_response(pending, True)], conversation=conversation)
    evidence.write("APPROVAL_RESUME", conversation_id=conversation, approval_id=pending["id"],
                   approved=True, output=item_summaries(approved), tool_names=tool_names(approved))
    return approved


def ensure_status(evidence, client, conversation, response, service="orders", verifier="service_status"):
    if has_tool(response, "operations___" + verifier) or has_tool(response, verifier):
        return response
    return turn(evidence, client, conversation, "status-explicit",
                f"Now call operations___{verifier} exactly once with service_name {service}. "
                "Use its exact result as the postcondition observation.")


def scenario_f(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "F_useful_recheck", "useful_recheck")
    try:
        turn(evidence, client, conversation, "health-before",
             "Call operations___service_status exactly once with service_name orders.")
        resumed = approved_restart(evidence, client, conversation)
        status = ensure_status(evidence, client, conversation, resumed)
        final = state(evidence, client, conversation, "useful-final")
        core = core_state(final)
        counts = external.snapshot()["counts"]
        outcome = core.get("last_postcondition_result") or {}
        assert counts.get("restart_service:orders", 0) == 1
        assert counts.get("service_status:orders", 0) == 2
        assert outcome.get("outcome") == "OUTCOME_VERIFIED", core
        assert core["recent_actions"][-1]["useful_recheck"] is True, core
        assert core["last_signals"]["postcondition_delta"] is True, core
        assert not core["contained"], core
        evidence.write("ASSERTIONS", scenario="F_useful_recheck", mode="ON",
                       tool_sequence=tool_names(resumed) + tool_names(status), useful_recheck=True,
                       postcondition=outcome, fuse_reason=core.get("fuse_reason"), detector_state=core,
                       run_id=core.get("run_id"), agent_session_id=final.get("agent_session_id"))
    finally:
        close_case(external, client, "F_useful_recheck")


def scenario_g(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "G_outcome_failure", "outcome_failure")
    try:
        resumed = approved_restart(evidence, client, conversation)
        status = ensure_status(evidence, client, conversation, resumed)
        final = state(evidence, client, conversation, "outcome-failure-final")
        core = core_state(final)
        counts = external.snapshot()["counts"]
        outcome = core.get("last_postcondition_result") or {}
        assert counts.get("restart_service:orders", 0) == 1
        assert counts.get("service_status:orders", 0) == 1
        assert outcome.get("outcome") == "POSTCONDITION_FAILED", core
        assert core["contained"] and core["fuse_reason"] == "POSTCONDITION_FAILED", core
        evidence.write("ASSERTIONS", scenario="G_outcome_failure", mode="ON",
                       tool_sequence=tool_names(resumed) + tool_names(status), postcondition=outcome,
                       fuse_reason=core["fuse_reason"], detector_state=core, run_id=core.get("run_id"),
                       agent_session_id=final.get("agent_session_id"))
    finally:
        close_case(external, client, "G_outcome_failure")


def scenario_h(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "H_budget_exhaustion", "no_progress_dns")
    try:
        responses = []
        for index in range(1, 12):
            responses.append(turn(
                evidence, client, conversation, f"budget-{index}",
                f"Call operations___dns_resolution exactly once for hostname budget-{index}. "
                "This turn requests ONLY that one DNS call. Do not call any other tool or perform "
                "follow-up investigation. Return the DNS result and end this turn; the test harness "
                "will send the next request."))
        final = state(evidence, client, conversation, "budget-final")
        core = core_state(final)
        assert core["contained"] and core["fuse_reason"] == "BUDGET_EXHAUSTED", core
        counts = external.snapshot()["counts"]
        assert sum(value for key, value in counts.items() if key.startswith("dns_resolution:")) == 10, counts
        assert counts == {f"dns_resolution:budget-{index}": 1 for index in range(1, 11)}, counts
        assert core["tool_call_count"] == 10, core
        evidence.write("ASSERTIONS", scenario="H_budget_exhaustion", mode="ON",
                       tool_sequence=[tool_names(item) for item in responses], fuse_reason=core["fuse_reason"],
                       detector_state=core, run_id=core.get("run_id"),
                       agent_session_id=final.get("agent_session_id"))
    finally:
        close_case(external, client, "H_budget_exhaustion")


def scenario_i(evidence: Phase2Evidence):
    external, client, conversation = new_case(evidence, "I_outcome_unknown", "outcome_unknown")
    try:
        resumed = approved_restart(evidence, client, conversation)
        ensure_status(evidence, client, conversation, resumed)
        core = core_state(state(evidence, client, conversation, "unknown-final"))
        counts = external.snapshot()["counts"]
        assert core["last_postcondition_result"]["outcome"] == "OUTCOME_UNKNOWN", core
        assert core["contained"] and core["fuse_reason"] == "OUTCOME_UNKNOWN", core
        assert counts.get("restart_service:orders") == 1 and counts.get("service_status:orders") == 1, counts
        turn(evidence, client, conversation, "unknown-post-trip",
             "Call operations___dns_resolution once with hostname api.reasonfuse.local.")
        assert external.snapshot()["counts"] == counts, "Dispatch occurred after unknown outcome"
        evidence.write("ASSERTIONS", scenario="I_outcome_unknown", detector_state=core, counts=counts,
                       status="stale HEALTHY rejected", post_trip_dispatches=0)
    finally:
        close_case(external, client, "I_outcome_unknown")


SCENARIOS = {
    "a-off": scenario_a,
    "b-on": scenario_b,
    "c-exact": scenario_c,
    "d-oscillation": scenario_d,
    "e-retrieval": scenario_e,
    "f-useful": scenario_f,
    "g-outcome-failure": scenario_g,
    "h-budget": scenario_h,
    "i-outcome-unknown": scenario_i,
}


def scenario_j(evidence):
    external, client, conversation = new_case(evidence, "J_database_recheck", "useful_recheck")
    try:
        turn(evidence, client, conversation, "database-before",
             "Call operations___database_health exactly once with service_name orders.")
        resumed = approved_restart(evidence, client, conversation, verifier="database_health")
        ensure_status(evidence, client, conversation, resumed, verifier="database_health")
        core = core_state(state(evidence, client, conversation, "database-final"))
        counts = external.snapshot()["counts"]
        assert counts.get("restart_service:orders") == 1 and counts.get("database_health:orders") == 2, counts
        assert core["last_postcondition_result"]["outcome"] == "OUTCOME_VERIFIED", core
        assert core["recent_actions"][-1]["useful_recheck"] is True and not core["contained"], core
        evidence.write("ASSERTIONS", scenario="J_database_recheck", detector_state=core, counts=counts)
    finally:
        close_case(external, client, "J_database_recheck")


SCENARIOS["j-database-recheck"] = scenario_j


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=[*SCENARIOS, "all"])
    parser.add_argument("--batch", default="hosted-" + datetime.now(timezone.utc).strftime("%Y%m%d"))
    parser.add_argument("--turn-delay", type=float, default=0,
                        help="Fixed pacing before each model turn; does not change core budgets")
    args = parser.parse_args()
    if not 0 <= args.turn_delay <= 60:
        parser.error("turn delay must be between 0 and 60 seconds")
    evidence = Phase2Evidence(args.batch, args.turn_delay)
    selected = list(SCENARIOS) if args.case == "all" else [args.case]
    failures = []
    for name in selected:
        evidence.write("SCENARIO_DRIVER", scenario=name)
        try:
            SCENARIOS[name](evidence)
            evidence.write("SCENARIO_RESULT", scenario=name, status="PASS", exit_code=0)
            print(f"PASS {name}")
        except Exception as error:
            failures.append(name)
            evidence.write("SCENARIO_RESULT", scenario=name, status="FAIL", exit_code=1,
                           error_type=type(error).__name__, error=str(error),
                           traceback=traceback.format_exc())
            print(f"FAIL {name}: {error}", file=sys.stderr)
    evidence.write("RESULT", status="PASS" if not failures else "FAIL", exit_code=0 if not failures else 1,
                   scenarios=selected, failures=failures)
    print(f"PHASE2_HOSTED_{'PASS' if not failures else 'FAIL'} {evidence.path}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
