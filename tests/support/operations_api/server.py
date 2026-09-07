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
            self.send_json(200, {"epoch": EPOCH, "counts": dict(COUNTS), "events": list(EVENTS)})

    def do_POST(self):
        global EPOCH
        if self.path == "/reset":
            if not self.admin_authorized():
                return self.send_json(403, {"error": "forbidden"})
            with LOCK:
                COUNTS.clear()
                EVENTS.clear()
                EPOCH = str(uuid.uuid4())
                return self.send_json(200, {"epoch": EPOCH, "counts": {}})
        routes = {
            "/dns-resolution": ("dns_resolution", "hostname", dns_resolution),
            "/restart-service": ("restart_service", "service_name", restart_service),
        }
        if self.path not in routes:
            return self.send_json(404, {"error": "not_found"})
        name, argument, function = routes[self.path]
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
            COUNTS[f"{name}:{value}"] += 1
            event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                     "epoch": EPOCH, "tool": name, "arguments": body,
                     "execution_count": COUNTS[f"{name}:{value}"]}
            EVENTS.append(event)
            print(json.dumps({"event": "EXTERNAL_TOOL_EXECUTION", **event}), flush=True)
            result = function(value)
        self.send_json(200, result)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
