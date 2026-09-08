"""Bounded, JSON-serializable ReasonFuse state owned by AgentSession."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

CORE_STATE_VERSION = "reasonfuse-core-v1"


@dataclass
class ReasonFuseState:
    run_id: str = field(default_factory=lambda: f"run-{uuid4().hex}")
    conversation_id: str | None = None
    agent_session_id: str | None = None
    framework_session_id: str | None = None
    trajectory_state: str = "ACTIVE"
    progress_state: str = "UNKNOWN"
    step_index: int = 0
    tool_call_count: int = 0
    side_effect_count: int = 0
    failed_call_count: int = 0
    blocked_proposal_count: int = 0
    denied_proposal_count: int = 0
    recent_actions: list[dict[str, Any]] = field(default_factory=list)
    recent_action_fingerprints: list[str] = field(default_factory=list)
    evidence_keys: list[str] = field(default_factory=list)
    retrieval_evidence_keys: list[str] = field(default_factory=list)
    world_state_snapshot: dict[str, Any] = field(default_factory=dict)
    todo_snapshot: dict[str, Any] = field(default_factory=dict)
    stall_counter: int = 0
    oscillation_counter: int = 0
    retrieval_churn_counter: int = 0
    last_objective_progress_step: int | None = None
    pending_postcondition: dict[str, Any] | None = None
    last_postcondition_result: dict[str, Any] | None = None
    run_contract_version: str = "reasonfuse-contract-v1"
    contract_limits: dict[str, Any] = field(default_factory=dict)
    reasonfuse_enabled: bool = True
    contained: bool = False
    fuse_reason: str | None = None
    verification_reserve_available: bool = False
    event_count: int = 0
    progress_history: list[bool] = field(default_factory=list)
    retrieval_attempts: list[dict[str, Any]] = field(default_factory=list)
    last_retrieval: dict[str, Any] = field(default_factory=dict)
    last_signals: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return only bounded primitive state suitable for provider persistence."""
        value = {
            "core_state_version": CORE_STATE_VERSION,
            **self.__dict__,
            "recent_actions": self.recent_actions[-32:],
            "recent_action_fingerprints": self.recent_action_fingerprints[-32:],
            "evidence_keys": self.evidence_keys[-64:],
            "retrieval_evidence_keys": self.retrieval_evidence_keys[-64:],
            "progress_history": self.progress_history[-32:],
            "retrieval_attempts": self.retrieval_attempts[-32:],
        }
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ReasonFuseState":
        if value.get("core_state_version") != CORE_STATE_VERSION:
            raise ValueError("unsupported ReasonFuse state version")
        allowed = {field for field in cls.__dataclass_fields__}
        data = {key: value[key] for key in allowed if key in value}
        data.setdefault("run_id", f"run-{uuid4().hex}")
        # A malformed persisted state must not become an implicit bypass.
        for name in ("step_index", "tool_call_count", "side_effect_count", "stall_counter",
                     "oscillation_counter", "retrieval_churn_counter", "event_count", "failed_call_count",
                     "blocked_proposal_count", "denied_proposal_count"):
            if type(data.get(name, 0)) is not int or data.get(name, 0) < 0:
                raise ValueError(f"invalid ReasonFuse state counter: {name}")
        for name in ("reasonfuse_enabled", "contained", "verification_reserve_available"):
            if name in data and type(data[name]) is not bool:
                raise ValueError(f"invalid {name}")
        return cls(**data)
