"""Deterministic evidence, world-state, retrieval and planning deltas."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

NOISY_WORLD_KEYS = {
    "timestamp_utc", "request_id", "trace_id", "execution_id", "operation_id",
    "counter", "execution_count", "event_id", "random_id",
}
WORLD_FIELDS = {"service_name", "service_health", "generation", "deployment_version",
                "database_state", "replica_count", "config_version", "dependency_health"}


def _stable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable(value[key]) for key in sorted(value) if key not in NOISY_WORLD_KEYS}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def normalize_world_state(value: dict[str, Any] | None) -> dict[str, Any]:
    return {key: _stable(item) for key, item in (value or {}).items() if key in WORLD_FIELDS
            or isinstance(item, dict) and any(field in item for field in WORLD_FIELDS)}


def world_state_delta(before: dict[str, Any] | None, after: dict[str, Any] | None) -> bool:
    return normalize_world_state(before) != normalize_world_state(after)


def _keys(value: Iterable[Any] | None) -> set[str]:
    return {str(item) for item in (value or [])}


def evidence_delta(before: Iterable[Any] | None, after: Iterable[Any] | None) -> bool:
    return bool(_keys(after) - _keys(before))


def retrieval_delta(before: dict[str, Any] | None, after: dict[str, Any] | None) -> bool:
    return retrieval_signature(before) != retrieval_signature(after)


def retrieval_signature(value: dict[str, Any] | None) -> tuple:
    value = value or {}
    return tuple(tuple(sorted(_keys(value.get(key)))) for key in
                 ("source_keys", "citation_ids", "chunk_ids", "content_hashes")) + (
                     value.get("knowledge_base_version"),)


@dataclass(frozen=True)
class ProgressSignals:
    evidence_delta: bool = False
    world_state_delta: bool = False
    retrieval_delta: bool = False
    todo_delta: bool = False
    postcondition_delta: bool = False
    evidence_keys: tuple[str, ...] = field(default_factory=tuple)
    retrieval_evidence_keys: tuple[str, ...] = field(default_factory=tuple)

    @property
    def objective_progress(self) -> bool:
        return any((self.evidence_delta, self.world_state_delta, self.retrieval_delta,
                    self.postcondition_delta))


def result_signals(previous: dict[str, Any], result: dict[str, Any],
                   previous_todo: dict[str, Any] | None = None,
                   todo: dict[str, Any] | None = None) -> ProgressSignals:
    evidence = tuple(str(item) for item in result.get("evidence_keys", []))
    retrieval_info = result.get("retrieval") or {}
    retrieval_keys = tuple(str(item) for item in retrieval_info.get("source_keys", []))
    return ProgressSignals(
        evidence_delta=evidence_delta(previous.get("evidence_keys", []), evidence),
        world_state_delta=("world_state" in result and
                           world_state_delta(previous.get("world_state"), result["world_state"])),
        retrieval_delta=("retrieval" in result and retrieval_delta(previous.get("retrieval"), retrieval_info)),
        todo_delta=todo is not None and (previous_todo or {}) != todo,
        # Only the local OutcomeVerifier may supply postcondition progress.
        postcondition_delta=False,
        evidence_keys=evidence,
        retrieval_evidence_keys=retrieval_keys,
    )


def normalized_result_class(result: Any) -> str:
    if not isinstance(result, dict):
        return type(result).__name__
    safe = {key: result[key] for key in sorted(result)
            if key not in NOISY_WORLD_KEYS and key not in {"world_state", "retrieval"}}
    return hashlib.sha256(json.dumps(safe, sort_keys=True, default=str).encode()).hexdigest()[:16]
