"""Prove that both deployed releases actually call Native Foundry IQ MCP."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scripts.support.validation import Evidence, HostedClient, output_text  # noqa: E402


def mcp_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in response.get("output", [])
        if item.get("type") in {"mcp_call", "mcp_call_output", "custom_tool_call", "custom_tool_call_output"}
        or (
            item.get("type") in {"function_call", "function_call_output"}
            and (
                "knowledge_base_retrieve" in json.dumps(item, ensure_ascii=False, default=str)
                or "rf-phase4-iq-001" in json.dumps(item, ensure_ascii=False, default=str)
                or "mcp://searchindex" in json.dumps(item, ensure_ascii=False, default=str)
            )
        )
    ]


def compact_mcp_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in items:
        encoded = json.dumps(item, ensure_ascii=False, default=str)
        result.append({
            "type": item.get("type"),
            "id": item.get("id"),
            "name": item.get("name"),
            "server_label": item.get("server_label"),
            "tool_name": item.get("tool_name"),
            "has_knowledge_base_retrieve": "knowledge_base_retrieve" in encoded,
            "has_expected_source_key": "rf-phase4-iq-001" in encoded,
            "serialized_length": len(encoded),
        })
    return result


def verify_role(evidence: Evidence, role: str) -> dict[str, Any]:
    project = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
    endpoint = f"{project}/agents/reasonfuse-phase1-{role}/endpoint/protocols/openai"
    client = HostedClient(evidence, base_url=endpoint)
    client.http.close()
    client.http = httpx.Client(timeout=httpx.Timeout(180, connect=30))
    try:
        conversation = client.conversation()
        response = client.turn(
            "Use the native Foundry IQ knowledge_base_retrieve tool exactly once to answer: "
            "What does ReasonFuse do when the same observed state produces no new evidence? "
            "Return the grounded answer and the returned source/citation; do not use a fixture.",
            conversation=conversation,
        )
        items = mcp_items(response)
        compact = compact_mcp_evidence(items)
        encoded = json.dumps(items, ensure_ascii=False, default=str)
        text = output_text(response)
        assert "knowledge_base_retrieve" in encoded, (
            f"{role} response contained no knowledge_base_retrieve MCP call; output types="
            f"{[item.get('type') for item in response.get('output', [])]}"
        )
        assert "rf-phase4-iq-001" in encoded or "BLOCK" in text, (
            f"{role} MCP result did not contain the version-pinned source or grounded policy answer"
        )
        evidence.write(
            "NATIVE_IQ_AGENT_ASSERTIONS",
            role=role,
            endpoint=endpoint,
            conversation_id=conversation,
            output_types=[item.get("type") for item in response.get("output", [])],
            mcp_items=compact,
            answer_excerpt=text[:2000],
            native_iq_source_key="rf-phase4-iq-001" if "rf-phase4-iq-001" in encoded else None,
        )
        return {
            "status": "PASS",
            "role": role,
            "conversation_id": conversation,
            "mcp_items": compact,
            "answer_excerpt": text[:500],
        }
    finally:
        client.close()


def main() -> int:
    evidence = Evidence("phase4_iq_agent_verify")
    started = time.time()
    try:
        results = {role: verify_role(evidence, role) for role in ("stable", "candidate")}
        result = {"status": "PASS", "roles": results, "elapsed_seconds": time.time() - started}
        evidence.write("RESULT", **result)
        print(json.dumps({"evidence": str(evidence.path), **result}, indent=2, default=str))
        return 0
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error))
        print(f"FAIL phase4_iq_agent_verify: {error}\nEvidence: {evidence.path}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
