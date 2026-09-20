"""Small deterministic Operations MCP server for bounded cloud validation.

This is intentionally a test fixture, not a production operations API.  It
keeps one in-memory service state so the Hosted Agent can demonstrate native
approval, fresh postcondition checks, and ReasonFuse containment without
touching any real infrastructure.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse


SERVICE_NAME = "orders"
VALID_MODES = {"verified", "failed", "unknown"}


class OperationsState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self, mode: str = "verified") -> dict[str, Any]:
        if mode not in VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
        with self._lock:
            self.mode = mode
            self.generation = "g1"
            self.health = "UNHEALTHY"
            self.restart_pending = False
            self.pending_generation = None
            self.restart_count = 0
            self.last_action = None
            return self._snapshot()

    def service_status(self, service_name: str) -> dict[str, Any]:
        if service_name != SERVICE_NAME:
            return {"resource": service_name, "status": "unknown", "error": "unknown service"}
        with self._lock:
            if self.restart_pending:
                self.restart_pending = False
                if self.mode == "verified":
                    self.health, self.generation = "HEALTHY", self.pending_generation or "g2"
                elif self.mode == "failed":
                    self.health, self.generation = "UNHEALTHY", self.pending_generation or "g2"
                else:
                    # Deliberately return an old generation: accepted action
                    # exists, but the external observation is insufficient.
                    return {
                        "resource": service_name,
                        "status": "stale",
                        "generation": self.generation,
                        "service_health": self.health,
                    }
            return {
                "resource": service_name,
                "generation": self.generation,
                "service_health": self.health,
                "world_state": {
                    "service_name": service_name,
                    "service_health": self.health,
                    "generation": self.generation,
                },
            }

    def restart_service(self, service_name: str) -> dict[str, Any]:
        if service_name != SERVICE_NAME:
            return {"accepted": False, "http_status": 404, "service_name": service_name}
        with self._lock:
            if self.restart_count:
                return {
                    "accepted": False,
                    "status_code": 409,
                    "resource": service_name,
                    "reason": "restart already executed for this test state",
                    "execution_count": self.restart_count,
                }
            self.restart_count = 1
            current_number = int(self.generation[1:]) if self.generation[1:].isdigit() else 1
            self.pending_generation = f"g{current_number + 1}"
            self.restart_pending = True
            self.last_action = "restart_service"
            return {
                "accepted": True,
                "status_code": 202,
                "resource": service_name,
                "operation_id": f"test-{service_name}-{self.pending_generation}",
                "generation": self.pending_generation,
                "execution_count": 1,
            }

    def _snapshot(self) -> dict[str, Any]:
        return {
            "service_name": SERVICE_NAME,
            "mode": self.mode,
            "service_health": self.health,
            "generation": self.generation,
            "restart_pending": self.restart_pending,
            "restart_count": self.restart_count,
            "last_action": self.last_action,
        }


state = OperationsState()
allowed_hosts = [
    value.strip()
    for value in os.environ.get("MCP_ALLOWED_HOSTS", "127.0.0.1:*,localhost:*").split(",")
    if value.strip()
]
mcp = FastMCP(
    "reasonfuse-operations",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
    ),
)


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True)


@mcp.tool(name="operations___service_status")
def service_status(service_name: str) -> str:
    """Read the current deterministic status for the orders test service."""
    return _json(state.service_status(service_name))


@mcp.tool(name="operations___restart_service")
def restart_service(service_name: str) -> str:
    """Submit one test restart; a later status call must verify the outcome."""
    return _json(state.restart_service(service_name))


def reset(mode: str = "verified") -> str:
    """Out-of-band test setup; deliberately not an MCP tool."""
    return _json(state.reset(mode))


@mcp.custom_route("/test/reset", methods=["POST"])
async def reset_fixture(request) -> JSONResponse:
    """Fixture administration outside the agent's MCP inventory."""
    try:
        body = await request.json()
        return JSONResponse(state.reset(body.get("mode", "verified")))
    except (ValueError, AttributeError):
        return JSONResponse({"error": "invalid reset mode"}, status_code=400)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "reasonfuse-operations"})


app = mcp.streamable_http_app()
