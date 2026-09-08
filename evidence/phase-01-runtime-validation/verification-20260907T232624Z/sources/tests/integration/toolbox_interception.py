import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.support.validation import HostedClient, Operations, run_case, runtime_state


def validate(evidence, blocked):
    external = Operations(evidence)
    external.reset()
    client = HostedClient(evidence)
    try:
        conversation = client.conversation()
        hostname = "blocked.reasonfuse.local" if blocked else "api.reasonfuse.local"
        response = client.turn(f"Call the dns_resolution tool exactly once for hostname {hostname}.",
                               conversation=conversation)
        assert not any(item.get("type") == "mcp_approval_request" for item in response.get("output", []))
        external.assert_counts({} if blocked else {f"dns_resolution:{hostname}": 1})
        state = runtime_state(client.turn("Call read_runtime_state and return its JSON.", conversation=conversation))
        audit = [event for event in state.get("middleware_events", []) if "dns_resolution" in event["tool_name"]]
        assert [event["event"] for event in audit] == ["BEFORE", "BLOCK" if blocked else "AFTER"], audit
        assert hostname in json.dumps(audit[0]["arguments"])
        assert ("BLOCKED" if blocked else "INCONCLUSIVE") in audit[-1]["result"], "Middleware result content not captured"
        evidence.write("ASSERTIONS", conversation_id=conversation, middleware=audit)
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["allow", "block"])
    args = parser.parse_args()
    run_case("spike02_toolbox_" + args.case, lambda e: validate(e, args.case == "block"))
