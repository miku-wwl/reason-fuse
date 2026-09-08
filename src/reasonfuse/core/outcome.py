"""Postcondition registry and deterministic outcome verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Postcondition:
    action: str
    verifier_tool: str
    resource_argument: str
    expected_field: str
    expected_value: Any


class PostconditionRegistry:
    def __init__(self) -> None:
        self._items = {
            "restart_service": Postcondition("restart_service", "service_status", "service_name",
                                             "service_health", "HEALTHY"),
        }

    def get(self, action: str) -> Postcondition:
        try:
            return self._items[action]
        except KeyError as exc:
            raise ValueError(f"no postcondition registered for {action}") from exc


class OutcomeVerifier:
    def __init__(self, registry: PostconditionRegistry | None = None) -> None:
        self.registry = registry or PostconditionRegistry()

    def verify(self, action: str, accepted_result: dict[str, Any], observation: dict[str, Any] | None,
               *, requested_resource: str) -> dict[str, Any]:
        if accepted_result.get("accepted") is not True:
            return {"outcome": "OUTCOME_UNKNOWN", "reason": "action_not_accepted"}
        postcondition = self.registry.get(action)
        if not isinstance(observation, dict) or observation.get("resource") != requested_resource:
            return {"outcome": "OUTCOME_UNKNOWN", "reason": "missing_or_mismatched_observation"}
        if observation.get("status") in {"timeout", "unavailable", "malformed", "stale"}:
            return {"outcome": "OUTCOME_UNKNOWN", "reason": observation["status"]}
        if accepted_result.get("generation") is not None and observation.get("generation") != accepted_result["generation"]:
            return {"outcome": "OUTCOME_UNKNOWN", "reason": "stale_or_missing_generation"}
        if observation.get(postcondition.expected_field) not in {"HEALTHY", "UNHEALTHY", "DEGRADED"}:
            return {"outcome": "OUTCOME_UNKNOWN", "reason": "malformed_observation"}
        if observation[postcondition.expected_field] == postcondition.expected_value:
            return {"outcome": "OUTCOME_VERIFIED", "reason": "fresh_postcondition_observation"}
        return {"outcome": "POSTCONDITION_FAILED", "reason": "expected_postcondition_not_met"}

    def verify_with(self, action: str, accepted_result: dict[str, Any], requested_resource: str,
                    observe: Callable[[str], dict[str, Any] | None]) -> dict[str, Any]:
        if not accepted_result.get("accepted", False):
            return {"outcome": "OUTCOME_UNKNOWN", "reason": "action_not_accepted"}
        try:
            observation = observe(requested_resource)
        except (TimeoutError, ConnectionError):
            observation = None
        return self.verify(action, accepted_result, observation,
                           requested_resource=requested_resource)
