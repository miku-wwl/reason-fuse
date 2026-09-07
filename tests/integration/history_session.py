import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.support.validation import HostedClient, output_text, run_case, runtime_state


def validate(evidence):
    client = HostedClient(evidence)
    try:
        conversation = client.conversation()
        first = client.turn(
            "My service is unhealthy. Remember incident ID INC-001. Also call read_runtime_state.",
            conversation=conversation,
        )
        first_state = runtime_state(first)
        second = client.turn(
            "What incident ID are we investigating? Also call read_runtime_state.",
            conversation=conversation,
        )
        second_state = runtime_state(second)
        assert "INC-001" in output_text(second), "Canonical conversation history was not recalled"
        assert first_state["reasonfuse_test_state"] == second_state["reasonfuse_test_state"] == "RF-STATE-001"
        assert first_state["agent_session_id"] == second_state["agent_session_id"]
        assert first_state["turn_number"] == 1 and second_state["turn_number"] == 2
        assert first_state["restored_at_turn_start"] is False
        assert second_state["restored_at_turn_start"] is True, "State was reinitialized, not restored"
        assert second_state["reasonfuse_test_counter"] == 7
        evidence.write("ASSERTIONS", conversation_id=conversation,
                        agent_session_id=second_state["agent_session_id"], first=first_state, second=second_state)
    finally:
        client.close()


if __name__ == "__main__":
    run_case("spike01_history_session", validate)
