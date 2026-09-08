"""Bounded deterministic loop, oscillation, churn and recheck detectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from .progress import retrieval_signature


@dataclass(frozen=True)
class DetectorResult:
    tripped: bool
    reason: str | None = None
    explanation: str = ""


def exact_loop(fingerprints: list[str], progress: list[bool], threshold: int = 3) -> DetectorResult:
    if threshold < 2:
        raise ValueError("exact loop threshold must be at least 2")
    if len(fingerprints) < threshold or len(progress) < threshold:
        return DetectorResult(False)
    recent = fingerprints[-threshold:]
    if len(set(recent)) == 1 and not any(progress[-threshold:]):
        return DetectorResult(True, "EXACT_LOOP", f"same fingerprint repeated {threshold} times without progress")
    return DetectorResult(False)


def oscillation(fingerprints: list[str], progress: list[bool], cycles: int = 2) -> DetectorResult:
    if cycles < 2:
        raise ValueError("oscillation cycles must be at least 2")
    width = cycles * 2
    if len(fingerprints) < width or len(progress) < width:
        return DetectorResult(False)
    recent = fingerprints[-width:]
    if recent[0] == recent[1]:
        return DetectorResult(False)
    if all(recent[index] == recent[index % 2] for index in range(width)) and not any(progress[-width:]):
        return DetectorResult(True, "OSCILLATING", f"period-2 cycle repeated {cycles} times without progress")
    return DetectorResult(False)


def retrieval_churn(retrieval_attempts: list[dict[str, Any]], threshold: int = 3) -> DetectorResult:
    if len(retrieval_attempts) < threshold:
        return DetectorResult(False)
    recent = retrieval_attempts[-threshold:]
    effective = [retrieval_signature(attempt) for attempt in recent]
    queries = [attempt.get("query") for attempt in recent]
    if len(set(queries)) > 1 and len(set(effective)) == 1:
        return DetectorResult(True, "RETRIEVAL_CHURN", f"{threshold} queries produced equivalent evidence")
    return DetectorResult(False)


@dataclass
class UsefulRecheckClassifier:
    pending_action: dict[str, Any] | None = None

    def accepted_side_effect(self, tool_name: str, resource: str, generation: str | None) -> None:
        self.pending_action = {"tool_name": tool_name, "resource": resource, "generation": generation,
                               "consumed": False}

    def denied_side_effect(self) -> None:
        # A denied proposal is not an accepted world-changing action.
        self.pending_action = None

    def classify(self, tool_name: str, resource: str, generation: str | None) -> DetectorResult:
        pending = self.pending_action
        if not pending or pending.get("consumed"):
            return DetectorResult(False, explanation="no pending postcondition obligation")
        useful = (tool_name in {"service_status", "database_health"}
                  and resource == pending["resource"]
                  and generation == pending["generation"])
        if useful:
            pending["consumed"] = True
            return DetectorResult(True, "USEFUL_RECHECK", "one bounded postcondition read after accepted side effect")
        return DetectorResult(False, explanation="resource or generation does not match pending obligation")
