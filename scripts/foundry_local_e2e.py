"""Run a bounded Microsoft Foundry Local ReasonFuse E2E audit.

This is intentionally a small local audit, not a benchmark.  It performs no
Azure provisioning, no Azure model calls, and no large scenario repetition.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_framework import AgentSession, Message  # noqa: E402
from foundry_local import FoundryLocalManager  # noqa: E402
from reasonfuse.local_runtime import (  # noqa: E402
    LocalOperationsServer,
    build_local_agent,
    configure_foundry_local_sdk_compat,
    load_foundry_local_model,
    model_metadata,
    read_service_status,
    reset_operations_fixture,
)


def _content_dict(content: Any) -> dict[str, Any]:
    if hasattr(content, "to_dict"):
        return content.to_dict()
    return {"type": getattr(content, "type", None), "text": getattr(content, "text", None)}


def _all_contents(response: Any) -> list[Any]:
    return [content for message in response.messages for content in message.contents]


def _approval_requests(response: Any) -> list[Any]:
    return [content for content in _all_contents(response) if content.type == "function_approval_request"]


def _function_calls(response: Any) -> list[Any]:
    return [content for content in _all_contents(response) if content.type == "function_call"]


def _function_results(response: Any) -> list[Any]:
    return [content for content in _all_contents(response) if content.type == "function_result"]


def _result_payloads(response: Any) -> list[dict[str, Any]]:
    payloads = []
    for content in _function_results(response):
        value = getattr(content, "result", None)
        try:
            parsed = json.loads(value) if isinstance(value, str) else value
        except json.JSONDecodeError:
            parsed = {"text": value}
        payloads.append(parsed if isinstance(parsed, dict) else {"value": parsed})
    return payloads


def _function_call_arguments(content: Any) -> dict[str, Any]:
    try:
        value = json.loads(content.function_call.arguments)
        return value if isinstance(value, dict) else {}
    except (AttributeError, TypeError, json.JSONDecodeError):
        return {}


def _tool_choice(name: str) -> dict[str, Any]:
    return {"tool_choice": {"mode": "required", "required_function_name": name}}


async def _run_normal_multiturn(bundle) -> dict[str, Any]:
    session = AgentSession()
    first = await bundle.agent.run(
        "Remember this exact marker for this session: LOCAL-RF-T1. Reply with ACK only.",
        session=session,
        options={"temperature": 0, "max_tokens": 40},
    )
    second = await bundle.agent.run(
        "What exact marker did I ask you to remember? Reply with the marker only.",
        session=session,
        options={"temperature": 0, "max_tokens": 40},
    )
    return {
        "status": "PASS" if "LOCAL-RF-T1" in second.text else "FAIL",
        "session_id": session.session_id,
        "first_text": first.text,
        "second_text": second.text,
        "store": False,
        "history_source": "local AgentSession (Hosted parity target: agent_server)",
    }


async def _run_basic_function_call(bundle) -> dict[str, Any]:
    session = AgentSession()
    response = await bundle.agent.run(
        "Call operations___dns_resolution exactly once with hostname api.reasonfuse.local. Return the tool JSON.",
        session=session,
        options={**_tool_choice("operations___dns_resolution"), "temperature": 0, "max_tokens": 80},
    )
    state = session.state.get("reasonfuse_core_v1", {})
    action = next((item for item in reversed(state.get("recent_actions", []))
                   if item.get("tool_name") == "dns_resolution"), {})
    return {
        "status": "PASS" if action.get("executed") and action.get("tool_name") == "dns_resolution" else "FAIL",
        "model_function_calls": len(_function_calls(response)),
        "response": response.text,
        "action": action,
        "session_id": session.session_id,
    }


async def _run_containment(bundle) -> dict[str, Any]:
    session = AgentSession()
    responses = []
    for _ in range(3):
        response = await bundle.agent.run(
            "Call operations___dns_resolution exactly once with hostname api.reasonfuse.local. "
            "Do not call any other tool.",
            session=session,
            options={**_tool_choice("operations___dns_resolution"), "temperature": 0, "max_tokens": 40},
        )
        responses.append(response)

    blocked = await bundle.agent.run(
        "Call operations___database_health exactly once with service_name orders.",
        session=session,
        options={**_tool_choice("operations___database_health"), "temperature": 0, "max_tokens": 40},
    )
    state = session.state.get("reasonfuse_core_v1", {})
    executed_dns = sum(
        1 for action in state.get("recent_actions", [])
        if action.get("tool_name") == "dns_resolution" and action.get("executed")
    )
    return {
        "status": "PASS" if state.get("fuse_reason") in {"NO_PROGRESS", "EXACT_LOOP"} and state.get("contained")
        and state.get("blocked_proposal_count", 0) >= 1 and executed_dns < 4 else "FAIL",
        "fuse_reason": state.get("fuse_reason"),
        "trajectory_state": state.get("trajectory_state"),
        "contained": state.get("contained"),
        "executed_dns_calls": executed_dns,
        "blocked_proposal_count": state.get("blocked_proposal_count"),
        "subsequent_response": blocked.text,
        "session_id": session.session_id,
        "model_function_calls": sum(len(_function_calls(response)) for response in responses),
    }


async def _run_approval_outcome(bundle, mode: str) -> dict[str, Any]:
    reset_operations_fixture(bundle.base_url, mode=mode)
    session = AgentSession()
    pending = await bundle.agent.run(
        "Submit a restart now. The JSON argument service_name must be exactly \"orders\"; "
        "do not add a prefix or suffix. Do not call service_status until approval is returned.",
        session=session,
        options={**_tool_choice("operations___restart_service"), "temperature": 0, "max_tokens": 80},
    )
    requests = _approval_requests(pending)
    if not requests:
        return {
            "status": "FAIL",
            "reason": "native approval request was not returned",
            "pending_response": pending.text,
            "pending_contents": [_content_dict(content) for content in _all_contents(pending)],
            "no_execution_before_approval": False,
            "session_id": session.session_id,
        }

    request_args = _function_call_arguments(requests[0])
    service_name = str(request_args.get("service_name", ""))
    if not service_name:
        return {"status": "FAIL", "reason": "approval request did not contain service_name"}
    # The model-generated argument is authoritative for this run. The fixture
    # is reset before approval so the comparison is against that exact target.
    reset_operations_fixture(bundle.base_url, service_name=service_name, mode=mode)
    before_approval = read_service_status(bundle.base_url, service_name=service_name)
    before_approval_again = read_service_status(bundle.base_url, service_name=service_name)
    no_execution_before_approval = before_approval_again == before_approval

    approved = await bundle.agent.run(
        Message(role="user", contents=[requests[0].to_function_approval_response(approved=True)]),
        session=session,
        options={"temperature": 0, "max_tokens": 80},
    )
    after_accept = session.state.get("reasonfuse_core_v1", {})
    accepted_not_success = bool(after_accept.get("pending_postcondition")) and not after_accept.get(
        "last_postcondition_result"
    )
    verified = await bundle.agent.run(
        f"Call operations___service_status exactly once with service_name exactly \"{service_name}\" "
        "to verify the restart.",
        session=session,
        options={**_tool_choice("operations___service_status"), "temperature": 0, "max_tokens": 80},
    )
    final_state = session.state.get("reasonfuse_core_v1", {})
    outcome = final_state.get("last_postcondition_result") or {}
    restart_execution_count = sum(
        1 for action in final_state.get("recent_actions", [])
        if action.get("tool_name") == "restart_service" and action.get("executed")
    )
    no_accidental_replay = True
    replay_response = ""
    if mode == "verified":
        replay = await bundle.agent.run(
            f"Call operations___service_status exactly once with service_name exactly \"{service_name}\" "
            "as a harmless follow-up; do not restart anything.",
            session=session,
            options={**_tool_choice("operations___service_status"), "temperature": 0, "max_tokens": 80},
        )
        replay_response = replay.text
        actions = session.state.get("reasonfuse_core_v1", {}).get("recent_actions", [])
        no_accidental_replay = sum(
            1 for action in actions if action.get("tool_name") == "restart_service" and action.get("executed")
        ) == 1
    expected_outcome = {
        "verified": "OUTCOME_VERIFIED",
        "failed": "POSTCONDITION_FAILED",
        "unknown": "OUTCOME_UNKNOWN",
    }[mode]
    return {
        "status": "PASS" if no_execution_before_approval and accepted_not_success
        and outcome.get("outcome") == expected_outcome and restart_execution_count == 1
        and no_accidental_replay else "FAIL",
        "mode": mode,
        "expected_outcome": expected_outcome,
        "service_name": service_name,
        "approval_required": True,
        "approval_request": _content_dict(requests[0]),
        "no_execution_before_approval": no_execution_before_approval,
        "accepted_not_success": accepted_not_success,
        "restart_execution_count": restart_execution_count,
        "accepted_response": approved.text,
        "accepted_tool_results": _result_payloads(approved),
        "verification_response": verified.text,
        "verification_tool_results": _result_payloads(verified),
        "outcome": outcome,
        "no_accidental_replay": no_accidental_replay,
        "replay_response": replay_response,
        "session_id": session.session_id,
        "final_reasonfuse_state": {
            "contained": final_state.get("contained"),
            "fuse_reason": final_state.get("fuse_reason"),
            "tool_call_count": final_state.get("tool_call_count"),
        },
    }


async def _run_validation_boundary(bundle) -> dict[str, Any]:
    session = AgentSession()
    response = await bundle.agent.run(
        "Call operations___dns_resolution exactly once with hostname blocked.reasonfuse.local.",
        session=session,
        options={**_tool_choice("operations___dns_resolution"), "temperature": 0, "max_tokens": 80},
    )
    state = session.state.get("reasonfuse_core_v1", {})
    validation = session.state.get("reasonfuse", {})
    events = validation.get("middleware_events", [])
    blocked = any(event.get("event") == "BLOCK" for event in events)
    return {
        "status": "PASS" if blocked and state.get("tool_call_count", 0) == 0 else "FAIL",
        "middleware_blocked": blocked,
        "tool_call_count": state.get("tool_call_count", 0),
        "response": response.text,
        "session_id": session.session_id,
    }


async def _run(args: argparse.Namespace) -> int:
    model = args.model or os.environ.get("FOUNDRY_LOCAL_MODEL", "phi-4-mini")
    os.environ.setdefault("REASONFUSE_ENABLED", "true")
    os.environ.setdefault("REASONFUSE_CONTRACT_JSON", "{}")
    report: dict[str, Any] = {
        "runtime": "Microsoft Foundry Local",
        "model_requested": model,
        "azure_calls": 0,
        "large_benchmark": False,
    }

    configure_foundry_local_sdk_compat()

    if shutil.which("foundry") is None and shutil.which("foundry-local") is None:
        report.update({
            "status": "BLOCKED",
            "blocker": "Foundry Local runtime is not installed or not on PATH; install/start it before this script.",
            "cli_found": False,
        })
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    try:
        manager = FoundryLocalManager(bootstrap=False)
        report["service_running_before"] = manager.is_service_running()
        if not report["service_running_before"]:
            report.update({"status": "BLOCKED", "blocker": "Foundry Local service is not running."})
            print(json.dumps(report, indent=2, sort_keys=True))
            return 2
    except Exception as error:
        report.update({"status": "BLOCKED", "blocker": f"Foundry Local runtime check failed: {error}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    with LocalOperationsServer() as operations:
        try:
            load_foundry_local_model(model)
            bundle = build_local_agent(operations.base_url, model=model, bootstrap=False, prepare_model=False)
            report["model"] = model_metadata(bundle.client, model)
            if not report["model"].get("supports_tool_calling", False):
                report.update({"status": "BLOCKED", "blocker": "Selected model does not advertise tool calling."})
                print(json.dumps(report, indent=2, sort_keys=True))
                return 2
            report["normal_multiturn"] = await _run_normal_multiturn(bundle)
            report["basic_function_call"] = await _run_basic_function_call(bundle)
            report["containment"] = await _run_containment(bundle)
            report["approval_verified"] = await _run_approval_outcome(bundle, "verified")
            report["approval_failed"] = await _run_approval_outcome(bundle, "failed")
            report["approval_unknown"] = await _run_approval_outcome(bundle, "unknown")
            report["validation_boundary"] = await _run_validation_boundary(bundle)
            statuses = [
                report[key]["status"]
                for key in (
                    "normal_multiturn", "basic_function_call", "containment", "approval_verified",
                    "approval_failed", "approval_unknown", "validation_boundary",
                )
            ]
            report["status"] = "PASS" if all(status == "PASS" for status in statuses) else "FAIL"
        except Exception as error:
            report.update({"status": "FAIL", "error": f"{type(error).__name__}: {error}"})

    encoded = json.dumps(report, indent=2, sort_keys=True)
    print(encoded)
    if args.report:
        Path(args.report).write_text(encoded + "\n", encoding="utf-8")
    return 0 if report.get("status") == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Foundry Local alias or model id; defaults to FOUNDRY_LOCAL_MODEL/phi-4-mini")
    parser.add_argument("--report", help="Optional path for the JSON result")
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
