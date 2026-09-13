"""Deterministic, resettable Operations fixture for the Phase 6 demo.

This is a demo-safe HTTP surface, not a production operations backend.  It
keeps the accepted side effect separate from the later observed service state
so the ReasonFuse outcome contract can be demonstrated without mutating a real
service.  The Terraform App Service command points at this file.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from typing import Any
from urllib.parse import parse_qs, urlparse


VALID_MODES = {"verified", "failed", "unknown"}


@dataclass
class ServiceState:
    health: str = "UNHEALTHY"
    generation: str = "g1"
    restart_pending: bool = False
    pending_generation: str | None = None
    verification_mode: str = "verified"


@dataclass
class OperationsFixture:
    """Small in-memory world model with deterministic reset semantics."""

    services: dict[str, ServiceState] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)

    def __post_init__(self) -> None:
        if not self.services:
            self.reset()

    def reset(self, service_name: str = "orders", mode: str = "verified") -> dict[str, Any]:
        if mode not in VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
        with self.lock:
            self.services[service_name] = ServiceState(verification_mode=mode)
            return {"reset": True, "resource": service_name, "mode": mode}

    def _service(self, service_name: str) -> ServiceState:
        with self.lock:
            return self.services.setdefault(service_name, ServiceState())

    def dns_resolution(self, hostname: str) -> dict[str, Any]:
        return {
            "hostname": hostname,
            "status": "RESOLVED",
            "evidence_keys": [f"dns:{hostname}"],
        }

    def database_health(self, service_name: str) -> dict[str, Any]:
        state = self._service(service_name)
        return {
            "resource": service_name,
            "database_state": "HEALTHY" if state.health == "HEALTHY" else "DEGRADED",
            "world_state": {
                "service_name": service_name,
                "database_state": "HEALTHY" if state.health == "HEALTHY" else "DEGRADED",
            },
        }

    def service_status(self, service_name: str) -> dict[str, Any]:
        state = self._service(service_name)
        with self.lock:
            if state.restart_pending:
                state.restart_pending = False
                if state.verification_mode == "verified":
                    state.health = "HEALTHY"
                    state.generation = state.pending_generation or state.generation
                elif state.verification_mode == "failed":
                    state.health = "UNHEALTHY"
                    state.generation = state.pending_generation or state.generation
                else:
                    # Deliberately return a stale generation and explicit stale
                    # status.  OutcomeVerifier must classify this as UNKNOWN.
                    return {
                        "resource": service_name,
                        "status": "stale",
                        "generation": state.generation,
                        "service_health": state.health,
                    }
            return {
                "resource": service_name,
                "generation": state.generation,
                "service_health": state.health,
                "world_state": {
                    "service_name": service_name,
                    "service_health": state.health,
                    "generation": state.generation,
                },
            }

    def restart_service(self, service_name: str) -> dict[str, Any]:
        state = self._service(service_name)
        with self.lock:
            next_generation = f"g{int(state.generation[1:]) + 1}" if state.generation[1:].isdigit() else "g2"
            state.restart_pending = True
            state.pending_generation = next_generation
            # No health claim is returned here.  Only service_status may prove
            # the postcondition after this accepted operation.
            return {
                "accepted": True,
                "status_code": HTTPStatus.ACCEPTED.value,
                "operation_id": f"demo-{service_name}-{next_generation}",
                "generation": next_generation,
            }

    def retrieval_fixture(self, query: str) -> dict[str, Any]:
        if "refined" in query.lower():
            source_keys = ["policy-A", "policy-B"]
            citation_ids = ["citation-1", "citation-2"]
        else:
            source_keys = ["policy-A"]
            citation_ids = ["citation-1"]
        return {
            "query": query,
            "retrieval": {
                "source_keys": source_keys,
                "citation_ids": citation_ids,
                "chunk_ids": ["chunk-1"],
                "knowledge_base_version": "phase6-fixture-v1",
            },
        }


FIXTURE = OperationsFixture()


class OperationsHandler(BaseHTTPRequestHandler):
    """HTTP adapter for the fixture; no framework dependency is required."""

    server_version = "ReasonFuseOperationsFixture/1"

    def _authorized(self) -> bool:
        expected = os.environ.get("OPERATIONS_ADMIN_KEY", "")
        return not expected or self.headers.get("X-Operations-Admin-Key") == expected

    def _write(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def _query(self) -> dict[str, str]:
        return {key: values[-1] for key, values in parse_qs(urlparse(self.path).query).items() if values}

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        query = self._query()
        try:
            if parsed.path == "/healthz":
                self._write({"status": "ok"})
            elif parsed.path == "/v1/dns_resolution":
                self._write(FIXTURE.dns_resolution(query.get("hostname", "api")))
            elif parsed.path == "/v1/database_health":
                self._write(FIXTURE.database_health(query.get("service_name", "orders")))
            elif parsed.path == "/v1/service_status":
                self._write(FIXTURE.service_status(query.get("service_name", "orders")))
            elif parsed.path == "/v1/retrieval_fixture":
                self._write(FIXTURE.retrieval_fixture(query.get("query", "incident")))
            else:
                self._write({"error": "not_found"}, HTTPStatus.NOT_FOUND)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            self._write({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if not self._authorized():
            self._write({"error": "approval_or_admin_key_required"}, HTTPStatus.FORBIDDEN)
            return
        parsed = urlparse(self.path)
        try:
            body = self._body()
            service_name = str(body.get("service_name", "orders"))
            if parsed.path == "/v1/reset":
                payload = FIXTURE.reset(service_name, str(body.get("mode", "verified")))
                self._write(payload)
            elif parsed.path == "/v1/restart_service":
                self._write(FIXTURE.restart_service(service_name), HTTPStatus.ACCEPTED)
            else:
                self._write({"error": "not_found"}, HTTPStatus.NOT_FOUND)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            self._write({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        # Keep demo logs deterministic and free of request headers/secrets.
        print(f"operations {self.command} {self.path.split('?', 1)[0]} {args[1]}")


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), OperationsHandler)
    print(f"ReasonFuse Operations fixture listening on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
