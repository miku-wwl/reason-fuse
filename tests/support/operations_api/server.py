"""Single-process external execution counters, independent of the agent runtime.

The epoch changes on process restart/reset; validators must reject an epoch change.
No database or durable store is required for these deliberately bounded experiments.
"""

import hmac
import json
import os
import threading
import uuid
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dns_resolution import dns_resolution
from restart_service import restart_service

LOCK = threading.Lock()
COUNTS = Counter()
EVENTS = []
EPOCH = str(uuid.uuid4())
ADMIN_KEY = os.environ["OPERATIONS_ADMIN_KEY"]
SCENARIO = "phase1"
SERVICE_HEALTH = {}
SERVICE_GENERATION = {}


def _status(service_name):
    health = SERVICE_HEALTH.get(service_name)
    if health is None:
        if SCENARIO == "outcome_failure":
            health = "UNHEALTHY"
        elif SCENARIO == "useful_recheck":
            health = "UNHEALTHY"
        else:
            health = "HEALTHY"
    generation = SERVICE_GENERATION.get(service_name, EPOCH + ":0")
    return {"resource": service_name, "service_name": service_name, "service_health": health,
            "generation": generation,
            "world_state": {"service_name": service_name, "service_health": health,
                            "generation": generation}}


def _record(tool, value, result):
    COUNTS[f"{tool}:{value}"] += 1
    event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "epoch": EPOCH,
             "tool": tool, "arguments": {"service_name" if tool != "retrieval_fixture" else "query": value},
             "execution_count": COUNTS[f"{tool}:{value}"]}
    EVENTS.append(event)
    print(json.dumps({"event": "EXTERNAL_TOOL_EXECUTION", **event}), flush=True)
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not log headers or credentials.

    def send_json(self, code, value):
        content = json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def admin_authorized(self):
        return hmac.compare_digest(self.headers.get("X-Validation-Key", ""), ADMIN_KEY)

    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"status": "ok"})
        if self.path != "/counters" or not self.admin_authorized():
            return self.send_json(404, {"error": "not_found"})
        with LOCK:
            self.send_json(200, {"epoch": EPOCH, "counts": dict(COUNTS), "events": list(EVENTS),
                                 "scenario": SCENARIO, "service_health": dict(SERVICE_HEALTH)})

    def do_POST(self):
        global EPOCH, SCENARIO
        if self.path == "/reset":
            if not self.admin_authorized():
                return self.send_json(403, {"error": "forbidden"})
            with LOCK:
                COUNTS.clear()
                EVENTS.clear()
                SCENARIO = "phase1"
                SERVICE_HEALTH.clear()
                SERVICE_GENERATION.clear()
                EPOCH = str(uuid.uuid4())
                return self.send_json(200, {"epoch": EPOCH, "counts": {}})
        if self.path == "/scenario":
            if not self.admin_authorized():
                return self.send_json(403, {"error": "forbidden"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length))
                scenario = body["scenario"]
                allowed = {"phase1", "no_progress_dns", "outcome_failure", "outcome_unknown", "useful_recheck", "retrieval_churn"}
                if scenario not in allowed:
                    raise ValueError("invalid_scenario")
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                return self.send_json(400, {"error": "invalid_scenario"})
            with LOCK:
                SCENARIO = scenario
                SERVICE_HEALTH.clear()
                SERVICE_GENERATION.clear()
                return self.send_json(200, {"scenario": SCENARIO, "epoch": EPOCH})
        routes = {
            "/dns-resolution": ("dns_resolution", "hostname"),
            "/restart-service": ("restart_service", "service_name"),
            "/service-status": ("service_status", "service_name"),
            "/database-health": ("database_health", "service_name"),
            "/retrieval-fixture": ("retrieval_fixture", "query"),
        }
        if self.path not in routes:
            return self.send_json(404, {"error": "not_found"})
        name, argument = routes[self.path]
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2048:
                raise ValueError("invalid_body_length")
            body = json.loads(self.rfile.read(length))
            value = body[argument]
            if set(body) != {argument} or not isinstance(value, str) or not 0 < len(value) <= 128:
                raise ValueError("invalid_arguments")
        except (ValueError, KeyError, TypeError):
            return self.send_json(400, {"error": "invalid_arguments"})
        with LOCK:
            if name == "dns_resolution":
                result = dns_resolution(value)
            elif name == "restart_service":
                SERVICE_GENERATION[value] = f"{EPOCH}:{COUNTS[f'restart_service:{value}'] + 1}"
                if SCENARIO in {"useful_recheck", "outcome_failure"}:
                    SERVICE_HEALTH[value] = "HEALTHY" if SCENARIO == "useful_recheck" else "UNHEALTHY"
                result = {**restart_service(value), "accepted": True, "generation": SERVICE_GENERATION[value]}
            elif name in {"service_status", "database_health"}:
                result = _status(value)
                if SCENARIO == "outcome_unknown":
                    result["status"] = "stale"
                    result["generation"] = EPOCH + ":stale"
                if name == "database_health":
                    result["resource"] = value
            else:
                result = {"query": value, "retrieval": {"source_keys": ["fixture-A", "fixture-B"],
                          "knowledge_base_version": "fixture-v1"}, "status": "FIXTURE_RESULT"}
            result = _record(name, value, result)
            if name == "restart_service":
                result["status_code"] = 202
        self.send_json(202 if name == "restart_service" else 200, result)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
