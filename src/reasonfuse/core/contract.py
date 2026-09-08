"""Trusted, versioned Phase 2 run contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RunContract:
    max_steps: int = 12
    max_tool_calls: int = 10
    max_stalled_steps: int = 2
    max_oscillation_cycles: int = 2
    max_retrieval_churn: int = 3
    max_side_effects: int = 1
    required_objective_progress_interval: int = 2
    require_postcondition_for_side_effects: bool = True
    version: str = "reasonfuse-contract-v1"

    def __post_init__(self) -> None:
        for name in ("max_steps", "max_tool_calls", "max_stalled_steps", "max_oscillation_cycles",
                     "max_retrieval_churn", "max_side_effects", "required_objective_progress_interval"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not 2 <= self.max_oscillation_cycles <= 16:
            raise ValueError("oscillation cycles must fit the bounded 32-action window")
        if not 2 <= self.max_retrieval_churn <= 32:
            raise ValueError("retrieval churn must fit the bounded 32-action window")
        if not isinstance(self.require_postcondition_for_side_effects, bool):
            raise ValueError("require_postcondition_for_side_effects must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_steps": self.max_steps,
            "max_tool_calls": self.max_tool_calls,
            "max_stalled_steps": self.max_stalled_steps,
            "max_oscillation_cycles": self.max_oscillation_cycles,
            "max_retrieval_churn": self.max_retrieval_churn,
            "max_side_effects": self.max_side_effects,
            "required_objective_progress_interval": self.required_objective_progress_interval,
            "require_postcondition_for_side_effects": self.require_postcondition_for_side_effects,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RunContract":
        data = dict(value)
        data.pop("version", None)
        return cls(**data, version=str(value.get("version", "reasonfuse-contract-v1")))

    def before_dispatch(self, *, steps: int, tool_calls: int, side_effects: int,
                       side_effect: bool, verification: bool, reserve_available: bool) -> str | None:
        # A required read occupies a slot INSIDE both total limits. Acceptance
        # cannot spend the last slot and borrow an unbounded verification call.
        slots = 2 if side_effect and self.require_postcondition_for_side_effects else 1
        if reserve_available and not verification:
            slots += 1
        if tool_calls + slots > self.max_tool_calls or steps + slots > self.max_steps:
            return "BUDGET_EXHAUSTED"
        if side_effect and side_effects >= self.max_side_effects:
            return "BUDGET_EXHAUSTED"
        return None
