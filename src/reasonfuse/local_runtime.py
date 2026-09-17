"""Small Foundry Local adapter for low-cost, local ReasonFuse E2E checks.

The Hosted Agent path remains in :mod:`reasonfuse.agent`.  This module only
swaps the model client and binds the existing deterministic HTTP fixture to
local Agent Framework function tools.  It deliberately does not duplicate the
ReasonFuse core or the Hosted Agent server.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from threading import Thread
from typing import Any

import httpx
from agent_framework import Agent, AgentModeProvider, FunctionTool, TodoProvider, tool
from agent_framework.foundry import FoundryLocalClient

from reasonfuse.core.middleware import ReasonFuseFunctionMiddleware
from reasonfuse.core.provider import CoreStateProvider
from reasonfuse.validation.middleware import HistoryAuditMiddleware, ValidationMiddleware
from reasonfuse.validation.session_state import ValidationStateProvider


def _current_foundry_local_endpoint() -> str | None:
    """Read the current Foundry Local CLI endpoint without starting a process."""

    try:
        result = subprocess.run(
            ["foundry", "server", "status", "--output", "json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        payload = json.loads(result.stdout) if result.returncode == 0 and result.stdout.strip() else {}
        urls = payload.get("webUrls", []) if payload.get("running") else []
        return urls[0] if urls else None
    except (OSError, TimeoutError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _start_foundry_local_server() -> str | None:
    """Start the current CLI daemon and return its endpoint when ready."""

    try:
        subprocess.run(["foundry", "server", "start"], check=False, timeout=30)
    except (OSError, TimeoutError):
        return None
    for _ in range(20):
        if endpoint := _current_foundry_local_endpoint():
            return endpoint
        time.sleep(0.25)
    return None


def configure_foundry_local_sdk_compat() -> None:
    """Bridge SDK 0.5.x's legacy ``service`` probe to CLI 0.10.x ``server``.

    The bridge is installed only by the local validation entry point.  The
    official ``FoundryLocalClient`` and ``FoundryLocalManager`` remain the
    actual client/manager; no Hosted or product runtime imports this helper.
    """

    from foundry_local import api as foundry_api
    from foundry_local.api import FoundryLocalManager
    from foundry_local.models import DeviceType, FoundryModelInfo

    if _current_foundry_local_endpoint() is None:
        return
    foundry_api.get_service_uri = _current_foundry_local_endpoint
    foundry_api.start_service = _start_foundry_local_server

    # SDK 0.5.x also expects the retired /foundry/list endpoint. The current
    # CLI exposes the same catalog as JSON, so adapt only this local process
    # and still return the SDK's FoundryModelInfo to FoundryLocalClient.
    if getattr(FoundryLocalManager, "_reasonfuse_cli_compat", False):
        return

    def cli_model_info(
        manager: FoundryLocalManager,
        alias_or_model_id: str,
        device: DeviceType | None = None,
        raise_on_not_found: bool = False,
    ) -> FoundryModelInfo | None:
        del manager
        try:
            result = subprocess.run(
                ["foundry", "model", "list", "--type", "chat", "--output", "json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            rows = json.loads(result.stdout).get("models", []) if result.returncode == 0 else []
        except (OSError, TimeoutError, json.JSONDecodeError, TypeError, ValueError):
            rows = []
        requested = alias_or_model_id.lower()
        candidates = [
            row for row in rows
            if str(row.get("id", "")).lower() == requested
            or str(row.get("alias", "")).lower() == requested
            or str(row.get("id", "")).lower().startswith(f"{requested}:")
        ]
        if device is not None:
            candidates = [row for row in candidates if str(row.get("device", "")).upper() == device.value]
        row = candidates[0] if candidates else None
        if row is None:
            if raise_on_not_found:
                raise ValueError(f"Model {alias_or_model_id} not found in the current Foundry Local catalog.")
            return None
        model_id = str(row["id"])
        version = model_id.rsplit(":", 1)[-1] if ":" in model_id else "0"
        device_value = str(row.get("device", "CPU")).upper()
        return FoundryModelInfo(
            alias=str(row.get("alias", alias_or_model_id)),
            id=model_id,
            version=version,
            execution_provider="",
            device_type=DeviceType(device_value),
            uri="",
            file_size_mb=int(row.get("fileSizeMb", 0)),
            supports_tool_calling=bool(row.get("supportsToolCalling", False)),
            prompt_template=None,
            provider="Microsoft",
            publisher="Microsoft",
            license=str(row.get("license", "")),
            task=str(row.get("type", "Chat")),
        )

    FoundryLocalManager.get_model_info = cli_model_info  # type: ignore[method-assign]
    FoundryLocalManager._reasonfuse_cli_compat = True  # type: ignore[attr-defined]


def load_foundry_local_model(model: str) -> None:
    """Load one already-downloaded model through the current Foundry CLI."""

    result = subprocess.run(["foundry", "model", "load", model], check=False, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"foundry model load failed with exit code {result.returncode}")


class LocalOperationsServer:
    """Run the repository's deterministic Operations fixture on an ephemeral port."""

    def __init__(self) -> None:
        from server import OperationsHandler

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), OperationsHandler)
        self._thread = Thread(target=self._server.serve_forever, name="reasonfuse-operations", daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_port}"

    def __enter__(self) -> "LocalOperationsServer":
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _get(base_url: str, path: str, params: dict[str, str]) -> str:
    response = httpx.get(f"{base_url}{path}", params=params, timeout=5)
    response.raise_for_status()
    return _json(response.json())


def _post(base_url: str, path: str, body: dict[str, str]) -> str:
    response = httpx.post(f"{base_url}{path}", json=body, timeout=5)
    response.raise_for_status()
    return _json(response.json())


def reset_operations_fixture(base_url: str, *, service_name: str = "orders", mode: str = "verified") -> dict[str, Any]:
    """Reset one fixture resource without bypassing its HTTP boundary."""

    response = httpx.post(
        f"{base_url}/v1/reset",
        json={"service_name": service_name, "mode": mode},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def read_service_status(base_url: str, *, service_name: str = "orders") -> dict[str, Any]:
    response = httpx.get(
        f"{base_url}/v1/service_status",
        params={"service_name": service_name},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def build_local_tools(base_url: str) -> dict[str, FunctionTool]:
    """Return local tools with the same logical names as the hosted operations."""

    @tool(name="operations___dns_resolution", approval_mode="never_require")
    def dns_resolution(hostname: str) -> str:
        """Resolve a hostname through the local read-only Operations fixture."""

        return _get(base_url, "/v1/dns_resolution", {"hostname": hostname})

    @tool(name="operations___database_health", approval_mode="never_require")
    def database_health(service_name: str) -> str:
        """Read database health through the local Operations fixture."""

        return _get(base_url, "/v1/database_health", {"service_name": service_name})

    @tool(name="operations___service_status", approval_mode="never_require")
    def service_status(service_name: str) -> str:
        """Read service status and generation through the local Operations fixture."""

        return _get(base_url, "/v1/service_status", {"service_name": service_name})

    @tool(name="operations___retrieval_fixture", approval_mode="never_require")
    def retrieval_fixture(query: str) -> str:
        """Read deterministic retrieval evidence from the local fixture."""

        return _get(base_url, "/v1/retrieval_fixture", {"query": query})

    @tool(name="operations___restart_service", approval_mode="always_require")
    def restart_service(service_name: str) -> str:
        """Submit a restart; a later service_status call must verify the outcome."""

        return _post(base_url, "/v1/restart_service", {"service_name": service_name})

    return {
        tool_item.name: tool_item
        for tool_item in (dns_resolution, database_health, service_status, retrieval_fixture, restart_service)
    }


@dataclass(frozen=True)
class LocalAgentBundle:
    """The local Agent plus its client, manager, fixture URL, and tools."""

    agent: Agent
    client: FoundryLocalClient
    base_url: str
    tools: dict[str, FunctionTool]


def build_local_agent(
    base_url: str,
    *,
    model: str | None = None,
    bootstrap: bool = True,
    prepare_model: bool = True,
) -> LocalAgentBundle:
    """Build a local Agent with the existing providers and middleware."""

    client = FoundryLocalClient(model=model, bootstrap=bootstrap, prepare_model=prepare_model)
    tools = build_local_tools(base_url)
    agent = Agent(
        client=client,
        name="ReasonFuseLocal",
        instructions=(
            "You are the local ReasonFuse validation agent. Use the named Operations tools exactly as requested. "
            "Never invent tool results. Do not claim an action succeeded without a fresh postcondition. "
            "When asked to restart service orders, submit operations___restart_service; a host approval is required. "
            "After approval, use operations___service_status to verify the result."
        ),
        default_options={"store": False},
        tools=list(tools.values()),
        context_providers=[
            TodoProvider(instructions="Use todo tools only when the user requests a todo list."),
            AgentModeProvider(default_mode="validate", mode_instructions={
                "validate": "Run only the requested bounded ReasonFuse validation action."
            }),
            ValidationStateProvider(),
            CoreStateProvider(),
        ],
        middleware=[ValidationMiddleware(), ReasonFuseFunctionMiddleware(), HistoryAuditMiddleware()],
    )
    return LocalAgentBundle(agent=agent, client=client, base_url=base_url, tools=tools)


def model_metadata(client: FoundryLocalClient, requested_model: str) -> dict[str, Any]:
    """Return bounded model metadata from the selected Foundry Local manager."""

    info = client.manager.get_model_info(requested_model)
    if info is None:
        raise ValueError(f"Foundry Local model {requested_model!r} was not found in the local catalog")
    fields = (
        "alias", "id", "version", "execution_provider", "device_type", "file_size_mb",
        "supports_tool_calling", "provider", "publisher", "task",
    )
    metadata: dict[str, Any] = {}
    for field in fields:
        if not hasattr(info, field):
            continue
        value = getattr(info, field)
        metadata[field] = value if isinstance(value, bool) else str(value)
    return metadata
