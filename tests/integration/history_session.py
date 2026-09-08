import sys
import uuid
import hashlib
import json
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.support.validation import HostedClient, output_text, run_case, runtime_state


def validate(evidence):
    client = HostedClient(evidence)
    try:
        conversation = client.conversation()
        marker = "RF-HISTORY-" + uuid.uuid4().hex
        first = client.turn(
            f"{marker}-T1 My service is unhealthy. Remember incident ID INC-001. Also call read_runtime_state.",
            conversation=conversation,
        )
        first_state = runtime_state(first)
        first_items = client.conversation_items(conversation)
        second = client.turn(
            f"{marker}-T2 What incident ID are we investigating? Also call read_runtime_state.",
            conversation=conversation,
        )
        second_state = runtime_state(second)
        second_items = client.conversation_items(conversation)
        assert "INC-001" in output_text(second), "Canonical conversation history was not recalled"
        assert first_state["reasonfuse_test_state"] == second_state["reasonfuse_test_state"] == "RF-STATE-001"
        assert first_state["agent_session_id"] == second_state["agent_session_id"]
        assert first_state["turn_number"] == 1 and second_state["turn_number"] == 2
        assert first_state["restored_at_turn_start"] is False
        assert second_state["restored_at_turn_start"] is True, "State was reinitialized, not restored"
        assert second_state["reasonfuse_test_counter"] == 7
        assert first["agent_session_id"] == second["agent_session_id"] == second_state["platform_session_id"]
        for state, items, turn in [(first_state, first_items, 1), (second_state, second_items, 2)]:
            assert state["downstream_service_session_id"] is None
            providers = state["history_providers"]
            assert len(providers) == 1 and providers[0]["class"] == "InMemoryHistoryProvider"
            assert providers[0]["state_at_turn_start"] is None, "Transient history survived a turn"
            expected = Counter({f"{marker}-T{i}": 1 for i in range(1, turn + 1)})
            assert Counter(m for msg in state["input_messages"] for m in msg["markers"]) == expected
            assert state["chat_requests"], "No actual model request observed"
            for request in state["chat_requests"] + state["previous_chat_requests"]:
                assert request["store"] is False and request["service_session_id"] is None
                # Repeated presentation across model-loop requests is legitimate; duplicates
                # within one request are not. Call and result may share an ID, once per type.
                keys = [(c["type"], c["call_id"]) for msg in request["messages"] for c in msg["contents"] if c["call_id"]]
                assert len(keys) == len(set(keys)), "Duplicate tool continuation in one model request"
                assistant_texts = [m["text_sha256"] for m in request["messages"] if m["role"] == "assistant" and m["text_sha256"] != hashlib.sha256(b'').hexdigest()]
                assert len(assistant_texts) == len(set(assistant_texts)), "Duplicate assistant transcript"
            assert Counter(m for msg in state["chat_requests"][0]["messages"] for m in msg["markers"]) == expected
            assert len({item["id"] for item in items}) == len(items), "Duplicate canonical item ID"
            assistant_items = [json.dumps(item["content"], sort_keys=True) for item in items if item.get("role") == "assistant"]
            assert len(assistant_items) == len(set(assistant_items)), "Duplicate canonical assistant message"
            tool_items = [(item["type"], item["call_id"]) for item in items if item.get("call_id")]
            assert len(tool_items) == len(set(tool_items)), "Duplicate canonical tool continuation"
            canonical_markers = Counter()
            for item in items:
                if item.get("role") == "user":
                    for part in item.get("content", []):
                        for i in range(1, turn + 1):
                            canonical_markers[f"{marker}-T{i}"] += part.get("text", "").count(f"{marker}-T{i}")
            assert +canonical_markers == expected
            calls = [item for item in items if item.get("type") == "function_call" and item.get("name") == "read_runtime_state"]
            assert len(calls) == turn, "Canonical tool call replay or missing call"
            evidence.write("HISTORY_AUDIT_ASSERTIONS", turn=turn, canonical_item_count=len(items),
                           canonical_state_calls=len(calls), unique_markers=dict(expected),
                           downstream_store=False, transient_history_empty=True)
        evidence.write("ASSERTIONS", conversation_id=conversation,
                        agent_session_id=second_state["agent_session_id"], first=first_state, second=second_state)
    finally:
        client.close()


if __name__ == "__main__":
    run_case("spike01_history_session", validate)
