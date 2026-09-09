"""Small real-HTTP validation client. No model mocks and no automatic POST retries."""

import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx
from azure.identity import AzureCliCredential, get_bearer_token_provider
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(os.environ.get(
    "REASONFUSE_EVIDENCE_ROOT",
    str(ROOT / "evidence" / "phase-01-runtime-validation"),
))
load_dotenv(ROOT / ".azure" / "rf-phase1-aue" / ".env")
load_dotenv(ROOT / ".env")


def now():
    return datetime.now(timezone.utc).isoformat()


class Evidence:
    def __init__(self, case):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.path = EVIDENCE_ROOT / "runs" / stamp[:8] / f"{stamp}-{case}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.write("START", case=case, command=sys.argv, region="australiaeast")

    def write(self, event, **fields):
        with self.path.open("a", encoding="utf-8") as out:
            out.write(json.dumps({"timestamp_utc": now(), "event": event, **fields}, default=str) + "\n")


def safe_headers(headers):
    result = {}
    for name, value in headers.items():
        if name.lower() in {
            "content-type", "date", "x-request-id", "apim-request-id", "request-id",
            "x-ms-request-id", "x-ms-agent-version", "x-agent-session-id", "traceparent",
            "x-reasonfuse-release", "transfer-encoding", "content-length",
        }:
            result[name] = value
        elif name.lower() == "set-cookie":
            result["set-cookie-name"] = value.split("=", 1)[0]
            result["set-cookie-sha256"] = hashlib.sha256(value.encode()).hexdigest()
    return result


class HostedClient:
    def __init__(self, evidence, *, base_url=None, token_provider=None):
        self.evidence = evidence
        project = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
        self.base = (base_url or f"{project}/agents/reasonfuse-phase1-stable/endpoint/protocols/openai").rstrip("/")
        self.credential = AzureCliCredential(process_timeout=60)
        self.token_provider = token_provider or get_bearer_token_provider(self.credential, "https://ai.azure.com/.default")
        # One cookie jar survives every turn of this client/session.
        self.http = httpx.Client(timeout=httpx.Timeout(600, connect=30))

    def headers(self):
        return {"Authorization": "Bearer " + self.token_provider()}

    def post(self, path, body):
        started = time.monotonic()
        self.evidence.write("REQUEST", method="POST", url=self.base + path, body=body,
                            cookie_names=[cookie.name for cookie in self.http.cookies.jar])
        response = self.http.post(self.base + path, params={"api-version": "v1"},
                                  json=body, headers=self.headers())
        try:
            result = response.json()
        except ValueError:
            result = {"non_json_body": response.text[:8000]}
        self.evidence.write("RESPONSE", status_code=response.status_code,
                            elapsed_seconds=time.monotonic() - started,
                            headers=safe_headers(response.headers), body=result)
        response.raise_for_status()
        if result.get("status") in {"failed", "cancelled"}:
            raise AssertionError(f"Hosted response {result['status']}: {result.get('error')}")
        return result

    def conversation(self):
        return self.post("/conversations", {})["id"]

    def conversation_items(self, conversation):
        items, after = [], None
        while True:
            params = {"api-version": "v1", "limit": 100, "order": "asc"}
            if after:
                params["after"] = after
            url = self.base + f"/conversations/{conversation}/items"
            response = self.http.get(url, params=params, headers=self.headers())
            body = response.json()
            self.evidence.write("CANONICAL_ITEMS", url=url, status_code=response.status_code,
                                headers=safe_headers(response.headers), body=body)
            response.raise_for_status()
            items.extend(body["data"])
            if not body.get("has_more"):
                return items
            cursor = body.get("last_id") or body["data"][-1]["id"]
            assert cursor != after, "Canonical pagination did not advance"
            after = cursor

    def turn(self, text, *, conversation=None, previous=None, session=None):
        body = {"input": text, "stream": False, "store": True}
        if conversation:
            body["conversation"] = conversation
        if previous:
            body["previous_response_id"] = previous
        if session:
            body["agent_session_id"] = session
        return self.post("/responses", body)

    def close(self):
        self.http.close()
        self.credential.close()


def output_text(response):
    return "\n".join(content.get("text", "")
                     for item in response.get("output", []) if item.get("type") == "message"
                     for content in item.get("content", []) if content.get("type") == "output_text")


def runtime_state(response):
    # Only trust the actual tool output, never a model-written JSON answer.
    for item in response.get("output", []):
        if item.get("type") not in {"function_call_output", "custom_tool_call_output", "mcp_call"}:
            continue
        raw = item.get("output")
        try:
            value = json.loads(raw) if isinstance(raw, str) else raw
        except ValueError:
            continue
        if isinstance(value, dict) and "reasonfuse_test_state" in value:
            return value
    raise AssertionError("No authoritative read_runtime_state tool output in Responses payload")


def run_case(name, callback):
    evidence = Evidence(name)
    try:
        callback(evidence)
    except Exception as error:
        evidence.write("RESULT", status="FAIL", error_type=type(error).__name__, error=str(error),
                        traceback=traceback.format_exc(), exit_code=1)
        print(f"FAIL {name}: {error}\nEvidence: {evidence.path}")
        raise SystemExit(1) from error
    evidence.write("RESULT", status="PASS", exit_code=0, evidence_layer="real_hosted_integration")
    print(f"PASS {name}\nEvidence: {evidence.path}")


class Operations:
    def __init__(self, evidence):
        self.evidence = evidence
        self.base = os.environ["OPERATIONS_ENDPOINT"].rstrip("/")
        self.headers = {"X-Validation-Key": os.environ["OPERATIONS_ADMIN_KEY"]}
        self.epoch = None

    def reset(self):
        response = httpx.post(self.base + "/reset", headers=self.headers, timeout=90)
        response.raise_for_status()
        result = response.json()
        self.epoch = result["epoch"]
        self.evidence.write("COUNTER_RESET", result=result)
        return result

    def snapshot(self):
        response = httpx.get(self.base + "/counters", headers=self.headers, timeout=90)
        response.raise_for_status()
        result = response.json()
        self.evidence.write("EXTERNAL_COUNTERS", result=result)
        assert self.epoch == result["epoch"], "External counter epoch changed; zero cannot prove non-execution"
        return result

    def assert_counts(self, expected):
        actual = self.snapshot()["counts"]
        assert actual == expected, f"Expected external counts {expected}, got {actual}"


def approval_request(response):
    pending = [item for item in response.get("output", []) if item.get("type") == "mcp_approval_request"]
    assert len(pending) == 1, f"Expected one pending approval; received {len(pending)}"
    return pending[0]


def approval_response(pending, approve):
    return {"type": "mcp_approval_response", "approval_request_id": pending["id"], "approve": approve}
