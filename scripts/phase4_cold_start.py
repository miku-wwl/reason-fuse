"""Bounded cold-start proxy using a real Stable hosted-agent redeployment.

The Foundry hosted-agent surface does not expose a direct stop/start command.
This script therefore records an actual same-agent deployment/version change,
then continues the same conversation with a fresh client. It reports the
mechanism precisely so it cannot be mistaken for a fresh-client-only test.
"""

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
        "REASONFUSE_COLD_START_CHECKPOINT",
        r"C:\Users\weila\AppData\Local\Temp\reasonfuse-phase4-cold-start.json",
    )
)


def bounded_client(evidence: Evidence) -> HostedClient:
    client = HostedClient(evidence, base_url=os.environ["APIM_ENDPOINT"])
    client.http.close()
    client.http = httpx.Client(timeout=httpx.Timeout(150, connect=20))
    return client


def before(evidence: Evidence) -> None:
    client = bounded_client(evidence)
    try:
        conversation = client.conversation()
        marker = "RF-COLD-START-" + uuid.uuid4().hex[:12]
        response = client.turn(
            f"Remember marker {marker}. Then call read_runtime_state and return its JSON.",
            conversation=conversation,
        )
        state = runtime_state(response)
        checkpoint = {
            "conversation_id": conversation,
            "marker": marker,
            "pre_turn": state.get("turn_number"),
            "pre_state": state.get("reasonfuse_test_state"),
            "pre_agent_version": (response.get("agent_reference") or {}).get("version"),
            "pre_platform_session_id": response.get("agent_session_id"),
        }
        CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
        CHECKPOINT.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
        evidence.write("COLD_START_BEFORE", **checkpoint)
        print(json.dumps({"phase": "before", "checkpoint": str(CHECKPOINT), **checkpoint}, indent=2))
    finally:
        client.close()


def after(evidence: Evidence) -> int:
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    client = bounded_client(evidence)
    try:
        response = client.turn(
            f"What marker did I ask you to remember? Return it, then call read_runtime_state.",
            conversation=checkpoint["conversation_id"],
        )
        state = runtime_state(response)
        text = output_text(response)
        post_version = (response.get("agent_reference") or {}).get("version")
        passed = (
            checkpoint["marker"] in text
            and state.get("reasonfuse_test_state") == checkpoint["pre_state"]
            and state.get("turn_number", 0) > checkpoint["pre_turn"]
            and post_version
            and post_version != checkpoint["pre_agent_version"]
        )
        result = {
            "status": "PASS" if passed else "NOT VERIFIED",
            "mechanism": "same Stable hosted-agent redeployment/version replacement",
            "conversation_id": checkpoint["conversation_id"],
            "marker_recalled": checkpoint["marker"] in text,
            "pre_agent_version": checkpoint["pre_agent_version"],
            "post_agent_version": post_version,
            "pre_platform_session_id": checkpoint["pre_platform_session_id"],
            "post_platform_session_id": response.get("agent_session_id"),
            "pre_turn": checkpoint["pre_turn"],
            "post_turn": state.get("turn_number"),
            "state_restored": state.get("reasonfuse_test_state") == checkpoint["pre_state"],
            "limitation": "Deployment/version replacement is the documented bounded equivalent; no direct hosted-agent stop/start API was available.",
        }
        evidence.write("COLD_START_AFTER", **result)
        evidence.write("RESULT", status=result["status"], mechanism=result["mechanism"])
        print(json.dumps({"phase": "after", **result}, indent=2))
        return 0 if passed else 2
    finally:
        client.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["before", "after"])
    args = parser.parse_args()
    evidence = Evidence("phase4_cold_start_" + args.phase)
    try:
        if args.phase == "before":
            before(evidence)
            return 0
        return after(evidence)
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error))
        print(f"FAIL phase4_cold_start_{args.phase}: {error}\nEvidence: {evidence.path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
