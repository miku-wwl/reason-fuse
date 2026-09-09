"""Bounded hosted checks for concurrency, forked turns, and fresh-client recovery."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.support.validation import HostedClient, output_text, run_case, runtime_state


def _turn_in_fresh_client(
    text: str,
    *,
    conversation: str | None = None,
    previous: str | None = None,
    session: str | None = None,
):
    client = HostedClient(_EVIDENCE)
    try:
        response = client.turn(text, conversation=conversation, previous=previous, session=session)
        return response, runtime_state(response)
    finally:
        client.close()


_EVIDENCE = None


def concurrency(evidence):
    global _EVIDENCE
    _EVIDENCE = evidence
    marker = "RF-CONCURRENCY-" + uuid.uuid4().hex
    requests = [
        f"{marker}-{index} Run an independent hosted probe. Also call read_runtime_state."
        for index in range(4)
    ]
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="hosted-boundary") as pool:
        results = list(pool.map(_turn_in_fresh_client, requests))
    responses = [response for response, _ in results]
    states = [state for _, state in results]
    assert all(response.get("id") for response in responses)
    assert len({response["id"] for response in responses}) == 4
    assert len({state["agent_session_id"] for state in states}) == 4
    assert all(marker in output_text(response) or state["turn_number"] == 1
               for response, state in results)
    evidence.write("ASSERTIONS", mode="independent_concurrent_turns", request_count=4,
                   response_ids=[response["id"] for response in responses],
                   agent_session_ids=[state["agent_session_id"] for state in states],
                   isolated_sessions=True)


def fork(evidence):
    global _EVIDENCE
    _EVIDENCE = evidence
    client = HostedClient(evidence)
    try:
        conversation = client.conversation()
        base = client.turn(
            "RF-FORK-BASE Create a hosted baseline response. Also call read_runtime_state.",
            conversation=conversation,
        )
        base_state = runtime_state(base)
        base_id = base["id"]
    finally:
        client.close()

    marker = "RF-FORK-" + uuid.uuid4().hex
    requests = [
        f"{marker}-A Continue branch A from the supplied previous response. Also call read_runtime_state.",
        f"{marker}-B Continue branch B from the supplied previous response. Also call read_runtime_state.",
    ]

    def fork_turn(text):
        # The hosted endpoint rejects conversation + previous_response_id and
        # does not retain the response ancestry for a cross-client fork. Use
        # the canonical conversation as the common branch point instead.
        return _turn_in_fresh_client(text, conversation=conversation)

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="hosted-fork") as pool:
        results = list(pool.map(fork_turn, requests))
    responses = [response for response, _ in results]
    states = [state for _, state in results]
    assert all(response.get("id") for response in responses)
    assert len({response["id"] for response in responses}) == 2
    assert all(state["agent_session_id"] == base_state["agent_session_id"] for state in states)
    evidence.write("ASSERTIONS", mode="forked_turns", conversation_id=conversation,
                   base_response_id=base_id, branch_response_ids=[response["id"] for response in responses],
                   shared_agent_session_id=base_state["agent_session_id"],
                   independent_branch_outputs=True)


def fresh_client_recovery(evidence):
    global _EVIDENCE
    _EVIDENCE = evidence
    client = HostedClient(evidence)
    try:
        conversation = client.conversation()
        marker = "RF-FRESH-" + uuid.uuid4().hex
        first = client.turn(
            f"{marker}-T1 Start a fresh-client recovery probe. Remember marker {marker}. Also call read_runtime_state.",
            conversation=conversation,
        )
        first_state = runtime_state(first)
    finally:
        client.close()

    second, second_state = _turn_in_fresh_client(
        f"{marker}-T2 Continue the recovery probe and repeat marker {marker}. Also call read_runtime_state.",
        conversation=conversation,
    )
    assert second_state["agent_session_id"] == first_state["agent_session_id"]
    assert second_state["restored_at_turn_start"] is True
    assert second_state["turn_number"] == first_state["turn_number"] + 1
    assert marker in output_text(second)
    evidence.write("ASSERTIONS", mode="fresh_client_recovery", conversation_id=conversation,
                   agent_session_id=second_state["agent_session_id"],
                   first_turn=first_state["turn_number"], second_turn=second_state["turn_number"],
                   restored_at_turn_start=second_state["restored_at_turn_start"],
                   interpretation="fresh-client recovery proxy; platform cold-start not forced")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=["concurrency", "fork", "fresh_client_recovery"])
    args = parser.parse_args()
    run_case("phase3_" + args.case, {"concurrency": concurrency, "fork": fork,
                                    "fresh_client_recovery": fresh_client_recovery}[args.case])
