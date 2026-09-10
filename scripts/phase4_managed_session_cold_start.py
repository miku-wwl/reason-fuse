"""Use the official hosted-session stop/resume lifecycle for cold-start proof."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.support.validation import Evidence, HostedClient, output_text, runtime_state


CHECKPOINT = Path(
    os.environ.get(
        "REASONFUSE_MANAGED_COLD_CHECKPOINT",
        r"C:\Users\weila\AppData\Local\Temp\reasonfuse-phase4-managed-cold.json",
    )
)


def bounded_client(evidence: Evidence) -> HostedClient:
    instance = HostedClient(evidence, base_url=os.environ["APIM_ENDPOINT"])
    instance.http.close()
    instance.http = httpx.Client(timeout=httpx.Timeout(150, connect=20))
    return instance


def before(evidence: Evidence) -> None:
    session_id = os.environ["REASONFUSE_MANAGED_SESSION_ID"]
    instance = bounded_client(evidence)
    try:
        conversation_response = instance.post("/conversations", {"agent_session_id": session_id})
        conversation = conversation_response["id"]
        marker = "RF-MANAGED-COLD-" + uuid.uuid4().hex[:12]
        response = instance.turn(
            f"Remember marker {marker}. Then call read_runtime_state and return its JSON.",
            conversation=conversation,
            session=session_id,
        )
        state = runtime_state(response)
        checkpoint = {
            "conversation_id": conversation,
            "marker": marker,
            "managed_session_id": session_id,
            "pre_turn": state.get("turn_number"),
            "pre_state": state.get("reasonfuse_test_state"),
            "pre_response_session_id": response.get("agent_session_id"),
            "pre_agent_version": (response.get("agent_reference") or {}).get("version"),
        }
        CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
        CHECKPOINT.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
        evidence.write("MANAGED_COLD_BEFORE", **checkpoint)
        print(json.dumps({"phase": "before", **checkpoint}, indent=2))
    finally:
        instance.close()


def after(evidence: Evidence) -> int:
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    instance = bounded_client(evidence)
    try:
        response = instance.turn(
            "What marker did I ask you to remember? Return it, then call read_runtime_state.",
            conversation=checkpoint["conversation_id"],
            session=checkpoint["managed_session_id"],
        )
        state = runtime_state(response)
        text = output_text(response)
        result = {
            "status": "PASS" if (
                checkpoint["marker"] in text
                and state.get("reasonfuse_test_state") == checkpoint["pre_state"]
                and state.get("turn_number", 0) > checkpoint["pre_turn"]
                and response.get("agent_session_id") == checkpoint["pre_response_session_id"]
            ) else "NOT VERIFIED",
            "mechanism": "official hosted session stop followed by resume on the same session",
            "conversation_id": checkpoint["conversation_id"],
            "managed_session_id": checkpoint["managed_session_id"],
            "marker_recalled": checkpoint["marker"] in text,
            "pre_response_session_id": checkpoint["pre_response_session_id"],
            "post_response_session_id": response.get("agent_session_id"),
            "pre_agent_version": checkpoint["pre_agent_version"],
            "post_agent_version": (response.get("agent_reference") or {}).get("version"),
            "pre_turn": checkpoint["pre_turn"],
            "post_turn": state.get("turn_number"),
            "state_restored": state.get("reasonfuse_test_state") == checkpoint["pre_state"],
            "platform_semantics": "stop terminates running compute while preserving the session volume; resume provisions compute again",
        }
        evidence.write("MANAGED_COLD_AFTER", **result)
        evidence.write("RESULT", status=result["status"], mechanism=result["mechanism"])
        print(json.dumps({"phase": "after", **result}, indent=2))
        return 0 if result["status"] == "PASS" else 2
    finally:
        instance.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["before", "after"])
    args = parser.parse_args()
    evidence = Evidence("phase4_managed_session_cold_" + args.phase)
    try:
        if args.phase == "before":
            before(evidence)
            return 0
        return after(evidence)
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error))
        print(f"FAIL phase4_managed_session_cold_{args.phase}: {error}\nEvidence: {evidence.path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
