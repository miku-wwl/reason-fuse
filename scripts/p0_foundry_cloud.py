"""Bounded manual cloud-gate driver; never schedules a benchmark or deployment.

Credentials stay in memory. Private endpoint/session references stay under the
ignored .tools directory; committed evidence has stable redacted identifiers.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time

import httpx
from azure.identity import AzureCliCredential
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".tools/p0-cloud/private"
EVIDENCE = ROOT / "docs/evidence/p0-foundry"
CLAIM = "UNSUPPORTED_CLOUD_SUCCESS"


def utc():
    return datetime.now(timezone.utc).isoformat()


def alias(value):
    return "redacted-" + hashlib.sha256(value.encode()).hexdigest()[:16]


def sanitize(value):
    if isinstance(value, dict):
        return {key: ("<redacted>" if any(part in key.lower() for part in
                    ("authorization", "access_token", "connection_string", "password", "secret"))
                     else alias(item) if key.lower() in {"session_id", "agent_session_id", "platform_session_id", "x-agent-session-id", "x-ms-agent-session-id"}
                     and isinstance(item, str) and not item.startswith("redacted-")
                     else sanitize(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r'((?:agent_session_id|platform_session_id)\\*"\s*:\s*\\*")([0-9a-f]{60,64})(\\*")',
                       lambda m: m[1] + alias(m[2]) + m[3], value)
        value = re.sub(r"https?://[^\s\"'<>\\]+", lambda m: alias(m[0]), value)
        value = re.sub(r"[A-Za-z0-9.-]+\.(?:services\.ai\.azure\.com|azurecontainerapps\.io|azurecr\.io)",
                       lambda m: alias(m[0]), value)
        value = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                       lambda m: alias(m[0]), value, flags=re.I)
        value = re.sub(r"\b(?:caresp|mcpr|conv|sess)_[A-Za-z0-9_-]+", lambda m: alias(m[0]), value)
        value = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "<redacted-email>", value)
    return value


def save(name, payload):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError("Evidence name must be a simple label")
    PRIVATE.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    private = PRIVATE / f"{name}.json"
    public = EVIDENCE / f"{name}.json"
    if private.exists() or public.exists():
        raise FileExistsError(f"Evidence already exists: {name}")
    private.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    public.write_text(json.dumps(sanitize(payload), indent=2, default=str) + "\n", encoding="utf-8")


def load(name):
    return json.loads((PRIVATE / f"{name}.json").read_text(encoding="utf-8"))


def environment():
    return dotenv_values(ROOT / ".azure/reason-fuse/.env")


def fixture_base():
    return environment()["OPERATIONS_MCP_ENDPOINT"].removesuffix("/mcp")


async def snapshot(client):
    response = await client.get(fixture_base() + "/test/state")
    response.raise_for_status()
    return response.json()


def output_text(response):
    return "".join(content.get("text", "") for item in response.get("output", [])
                   for content in item.get("content", []) if isinstance(content, dict))


def summaries(response):
    items = response.get("output", [])
    return {"response_id": alias(response.get("id", "missing")), "status": response.get("status"),
            "item_types": [item.get("type") for item in items],
            "tools": [item.get("name") for item in items if item.get("name")],
            "approvals": sum(item.get("type") == "mcp_approval_request" for item in items),
            "text": output_text(response), "error": response.get("error")}


def request_body(args):
    body = {"input": args.input or "", "store": True, "stream": args.stream,
            "max_output_tokens": 5000}
    if args.conversation:
        body["conversation"] = load(args.conversation)["conversation"]["id"]
    if args.previous:
        previous = load(args.previous)["response"]
        if not args.conversation:
            body["previous_response_id"] = previous["id"]
        if args.approve is not None:
            approvals = [item for item in previous.get("output", []) if item.get("type") == "mcp_approval_request"]
            if not approvals:
                raise ValueError("Prior response has no native approval requests")
            body["input"] = [{"type": "mcp_approval_response", "approval_request_id": item["id"],
                              "approve": args.approve == "true"} for item in approvals]
            if args.input:
                body["input"].append({"role": "user", "content": args.input})
    return body


async def invoke(name, body, headers):
    payload = {"started_utc": utc(), "request": body, "agent_version": environment().get("AGENT_REASONFUSE_VERSION")}
    timeout = httpx.Timeout(240.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        payload["backend_before"] = await snapshot(client)
        started = time.monotonic()
        try:
            url = environment()["AGENT_REASONFUSE_RESPONSES_ENDPOINT"]
            if body["stream"]:
                events = []
                payload["events"] = events
                async with client.stream("POST", url, headers=headers, json=body) as response:
                    payload["http_status"] = response.status_code
                    payload["response_headers"] = {k: v for k, v in response.headers.items()
                                                   if k in {"date", "x-agent-session-id", "x-ms-agent-session-id", "x-ms-request-id"}}
                    if response.is_error:
                        payload["error_body"] = (await response.aread()).decode()
                        response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data:") or line[5:].strip() == "[DONE]":
                            continue
                        data = json.loads(line[5:].strip())
                        events.append({"received_utc": utc(), "elapsed_seconds": round(time.monotonic()-started, 6),
                                       "data": data})
                        if data.get("type") in {"response.completed", "response.failed", "response.incomplete"}:
                            payload["response"] = data.get("response", {})
                        if data.get("type") == "response.output_text.delta" and "first_text_backend" not in payload:
                            payload["first_text_backend"] = await snapshot(client)
                        if CLAIM in str(data.get("delta", "")):
                            payload["unsupported_claim_leaked"] = True
                if "response" not in payload:
                    raise RuntimeError("Stream ended without a terminal response")
            else:
                response = await client.post(url, headers=headers, json=body)
                payload["http_status"] = response.status_code
                payload["response_headers"] = {k: v for k, v in response.headers.items()
                                               if k in {"date", "x-agent-session-id", "x-ms-agent-session-id", "x-ms-request-id"}}
                payload["response"] = response.json()
                response.raise_for_status()
            payload["unsupported_claim_leaked"] = payload.get("unsupported_claim_leaked", False) or CLAIM in output_text(payload["response"])
        except Exception as error:
            payload["exception"] = {"type": type(error).__name__, "message": str(error)}
        finally:
            payload["elapsed_seconds"] = round(time.monotonic()-started, 6)
            payload["completed_utc"] = utc()
            payload["backend_after"] = await snapshot(client)
            save(name, payload)
    print(json.dumps(sanitize({"name": name, "http_status": payload.get("http_status"),
                              "elapsed_seconds": payload["elapsed_seconds"], "exception": payload.get("exception"),
                              "backend_counts": {key: payload["backend_after"][key] for key in
                                                 ("restart_count", "restart_attempt_count", "status_read_count")},
                              **summaries(payload.get("response", {}))}), indent=2))
    if payload.get("unsupported_claim_leaked"):
        raise RuntimeError("STOP: unsupported operational success was released")
    return payload


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["reset", "state", "invoke", "concurrent"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--input")
    parser.add_argument("--previous")
    parser.add_argument("--conversation", help="Evidence label of a created cloud conversation")
    parser.add_argument("--approve", choices=["true", "false"])
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--mode", choices=["verified", "failed", "unknown"], default="verified")
    args = parser.parse_args()
    if args.command in {"reset", "state"}:
        async with httpx.AsyncClient(timeout=30) as client:
            if args.command == "reset":
                result = await client.post(fixture_base() + "/test/reset", json={"mode": args.mode})
                result.raise_for_status()
            value = {"timestamp_utc": utc(), "operation": args.command, "state": await snapshot(client)}
            save(args.name, value)
            print(json.dumps(sanitize(value), indent=2))
        return
    with AzureCliCredential() as credential:
        token = credential.get_token("https://ai.azure.com/.default").token
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    body = request_body(args)
    if args.command == "concurrent":
        # Two actual HTTP requests start together with the same logical continuation.
        await asyncio.gather(invoke(args.name + "-a", body, headers), invoke(args.name + "-b", body, headers))
    else:
        await invoke(args.name, body, headers)


if __name__ == "__main__":
    asyncio.run(main())
