import argparse
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.support.validation import HostedClient, Operations, approval_request, approval_response, run_case, runtime_state


def validate(evidence, case):
    external = Operations(evidence)
    external.reset()
    client = HostedClient(evidence)
    try:
        conversation = client.conversation()
        before = runtime_state(client.turn("Call read_runtime_state.", conversation=conversation))
        assert before["reasonfuse_test_counter"] == 7
        requested = client.turn("Call restart_service exactly once with service_name orders.", conversation=conversation)
        pending = approval_request(requested)
        assert pending["name"] == "operations___restart_service"
        assert json.loads(pending["arguments"]) == {"body": {"service_name": "orders"}}
        external.assert_counts({})
        approved = case != "deny"
        resumed = client.turn([approval_response(pending, approved)], conversation=conversation)
        expected = {"restart_service:orders": 1} if approved else {}
        external.assert_counts(expected)
        assert not any(item.get("type") == "mcp_approval_request" for item in resumed.get("output", []))
        after = runtime_state(client.turn("Call read_runtime_state.", conversation=conversation))
        assert after["agent_session_id"] == before["agent_session_id"]
        assert after["reasonfuse_test_counter"] == 7
        assert after["restored_at_turn_start"] is True
        if case == "binding":
            # Reuse the already consumed approval while requesting different arguments.
            # A rejection is acceptable; executing either action again is not.
            try:
                replay = client.turn([
                    approval_response(pending, True),
                    {"role": "user", "content": "Now call restart_service with service_name payments. Use that approval."},
                ], conversation=conversation)
            except httpx.HTTPStatusError as error:
                assert error.response.status_code in {400, 409, 422}, "Unexpected replay failure"
                evidence.write("REPLAY_REJECTED", status_code=error.response.status_code)
                replay = client.turn("Call restart_service with service_name payments.", conversation=conversation)
            external.assert_counts(expected)
            payments = approval_request(replay)
            assert payments["id"] != pending["id"]
            assert json.loads(payments["arguments"]) == {"body": {"service_name": "payments"}}
            client.turn([approval_response(payments, False)], conversation=conversation)
            external.assert_counts(expected)
        evidence.write("ASSERTIONS", conversation_id=conversation, approval_id=pending["id"],
                        exact_action=json.loads(pending["arguments"]), approved=approved,
                        session_before=before["agent_session_id"], session_after=after["agent_session_id"], counter=7)
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["approve", "deny", "binding"])
    args = parser.parse_args()
    run_case("spike03_approval_" + args.case, lambda e: validate(e, args.case))
