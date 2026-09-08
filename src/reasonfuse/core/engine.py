"""Deterministic ReasonFuse decision engine used by local and hosted paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contract import RunContract
from .detectors import UsefulRecheckClassifier, exact_loop, oscillation, retrieval_churn
from .fingerprint import tool_fingerprint
from .progress import normalize_world_state, normalized_result_class, result_signals
from .state import ReasonFuseState

SIDE_EFFECT_TO_RESOURCE = {"restart_service": "service_name"}
VERIFICATION_TO_RESOURCE = {"service_status": "service_name", "database_health": "service_name"}


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str | None = None
    structured_result: dict[str, Any] | None = None


@dataclass(frozen=True)
class Observation:
    signals: dict[str, bool]
    objective_progress: bool
    trajectory_state: str
    progress_state: str
    fuse_reason: str | None
    executed: bool


class ReasonFuseEngine:
    def __init__(self, state: ReasonFuseState | None = None, contract: RunContract | None = None) -> None:
        self.state = state or ReasonFuseState()
        self.contract = contract or RunContract()
        self.state.run_contract_version = self.contract.version
        self._progress_history: list[bool] = list(self.state.progress_history)
        self._retrieval_attempts: list[dict[str, Any]] = list(self.state.retrieval_attempts)
        self._last_retrieval: dict[str, Any] = dict(self.state.last_retrieval)
        self._recheck = UsefulRecheckClassifier()
        if self.state.pending_postcondition:
            self._recheck.pending_action = dict(self.state.pending_postcondition)

    def pending_verification(self, tool_name: str, arguments: Any) -> bool:
        pending = self.state.pending_postcondition
        return bool(pending and not pending.get("consumed") and tool_name in VERIFICATION_TO_RESOURCE
                    and self._resource(tool_name, self._args(arguments)) == pending["resource"])

    def _stalled(self) -> bool:
        return self.state.stall_counter >= min(self.contract.max_stalled_steps,
                                              self.contract.required_objective_progress_interval)

    @staticmethod
    def _args(arguments: Any) -> dict[str, Any]:
        if hasattr(arguments, "model_dump"):
            return arguments.model_dump(mode="json")
        return dict(arguments or {})

    def _resource(self, tool_name: str, arguments: dict[str, Any]) -> str | None:
        name = SIDE_EFFECT_TO_RESOURCE.get(tool_name) or VERIFICATION_TO_RESOURCE.get(tool_name)
        body = arguments.get("body", arguments)
        return body.get(name) if isinstance(body, dict) and name else None

    def before_dispatch(self, tool_name: str, arguments: Any) -> Decision:
        args = self._args(arguments)
        fingerprint = tool_fingerprint(tool_name, args)
        verification = self.pending_verification(tool_name, args)
        side_effect = tool_name in SIDE_EFFECT_TO_RESOURCE
        if not self.state.reasonfuse_enabled:
            return Decision(True)
        if self.state.contained:
            return self._block(self.state.fuse_reason or "NO_PROGRESS", fingerprint)
        budget_reason = self.contract.before_dispatch(
            steps=self.state.step_index,
            tool_calls=self.state.tool_call_count,
            side_effects=self.state.side_effect_count,
            side_effect=side_effect,
            verification=verification,
            reserve_available=self.state.verification_reserve_available,
        )
        if budget_reason:
            return self._trip(budget_reason, fingerprint)
        if verification:
            return Decision(True)
        if self._stalled():
            return self._trip("NO_PROGRESS", fingerprint)
        loop = exact_loop(self.state.recent_action_fingerprints + [fingerprint],
                          self._progress_history + [False], threshold=3)
        if loop.tripped:
            return self._trip(loop.reason or "EXACT_LOOP", fingerprint)
        cycle = oscillation(self.state.recent_action_fingerprints + [fingerprint],
                            self._progress_history + [False], self.contract.max_oscillation_cycles)
        self.state.oscillation_counter = self.contract.max_oscillation_cycles if cycle.tripped else 0
        if cycle.tripped:
            return self._trip(cycle.reason or "OSCILLATING", fingerprint)
        if side_effect and self.state.side_effect_count >= self.contract.max_side_effects:
            return self._trip("BUDGET_EXHAUSTED", fingerprint)
        return Decision(True)

    def _block(self, reason: str, fingerprint: str | None = None) -> Decision:
        self.state.blocked_proposal_count += 1
        return Decision(False, reason, {"decision": "BLOCK", "trajectory_state": self.state.trajectory_state,
                                        "fuse_reason": reason, "objective_progress": False,
                                        "step": self.state.step_index,
                                        "fingerprint": fingerprint})

    def _trip(self, reason: str, fingerprint: str | None = None, *, completed: bool = False) -> Decision:
        self.state.contained = True
        self.state.trajectory_state = "STALLED"
        self.state.progress_state = "STALLED"
        self.state.fuse_reason = reason
        decision = self._block(reason, fingerprint)
        if completed:
            self.state.blocked_proposal_count -= 1
        return decision

    def record(self, tool_name: str, arguments: Any, result: dict[str, Any] | Any,
               *, executed: bool, side_effect: bool = False, approved: bool = True,
               todo_snapshot: dict[str, Any] | None = None) -> Observation:
        args = self._args(arguments)
        fingerprint = tool_fingerprint(tool_name, args)
        result = result if isinstance(result, dict) else {"value": str(result)}
        before = {"evidence_keys": self.state.evidence_keys,
                  "world_state": self.state.world_state_snapshot,
                  "retrieval": self._last_retrieval}
        previous_todo = dict(self.state.todo_snapshot)
        self.state.step_index += 1
        self.state.event_count += 1
        if executed:
            self.state.tool_call_count += 1
            if side_effect:
                self.state.side_effect_count += 1
        resource = self._resource(tool_name, args)
        verification = self.pending_verification(tool_name, args)
        # Permission comes from the persisted accepted action; the observation
        # may be stale or unhealthy and must still consume the one allowed read.
        useful = verification
        if verification:
            self.state.pending_postcondition["consumed"] = True
            self.state.verification_reserve_available = False
        observed = dict(result) if executed and not side_effect else {}
        if resource and isinstance(observed.get("world_state"), dict):
            # Keep resource observations separate; alternating tools/resources
            # must not look like a changing world merely by replacing snapshots.
            world = normalize_world_state(observed["world_state"])
            if world.get("service_name", resource) != resource:
                observed.pop("world_state")
            else:
                snapshot = dict(self.state.world_state_snapshot)
                snapshot[resource] = world
                observed["world_state"] = snapshot
        signals = result_signals(before, observed, previous_todo, todo_snapshot)
        self.state.evidence_keys = list(dict.fromkeys([*self.state.evidence_keys, *signals.evidence_keys]))[-64:]
        self.state.retrieval_evidence_keys = list(signals.retrieval_evidence_keys or self.state.retrieval_evidence_keys)[-64:]
        self.state.world_state_snapshot = observed.get("world_state", self.state.world_state_snapshot)
        if todo_snapshot is not None:
            self.state.todo_snapshot = todo_snapshot
        self.state.recent_action_fingerprints.append(fingerprint)
        self.state.recent_action_fingerprints = self.state.recent_action_fingerprints[-32:]
        self.state.recent_actions.append({"tool_name": tool_name, "fingerprint": fingerprint,
                                          "executed": executed, "side_effect": side_effect,
                                          "result_class": normalized_result_class(result),
                                          "useful_recheck": useful})
        self.state.recent_actions = self.state.recent_actions[-32:]
        self._progress_history.append(signals.objective_progress)
        self._progress_history = self._progress_history[-32:]
        self.state.progress_history = self._progress_history[-32:]
        if result.get("retrieval"):
            self._last_retrieval = result["retrieval"]
            self._retrieval_attempts.append({"query": result.get("query"), **result["retrieval"]})
            self._retrieval_attempts = self._retrieval_attempts[-32:]
            self.state.last_retrieval = self._last_retrieval
            self.state.retrieval_attempts = self._retrieval_attempts
        if signals.objective_progress:
            if not result.get("retrieval"):
                self._retrieval_attempts = []
                self.state.retrieval_attempts = []
                self.state.retrieval_churn_counter = 0
            self.state.stall_counter = 0
            self.state.last_objective_progress_step = self.state.step_index
            self.state.progress_state = "PROGRESS"
        else:
            self.state.stall_counter += 1
            self.state.progress_state = "STALLED" if self.state.stall_counter else "ACTIVE"
        if (side_effect and executed and approved and result.get("accepted") is True
                and self.contract.require_postcondition_for_side_effects):
            self.state.pending_postcondition = {"action": tool_name, "resource": resource,
                                                "generation": result.get("generation"), "consumed": False,
                                                "accepted_result": result,
                                                "before_state": self.state.world_state_snapshot.get(resource)}
            self.state.verification_reserve_available = True
            self._recheck.accepted_side_effect(tool_name, resource or "", result.get("generation"))
        if signals.retrieval_delta is False and result.get("retrieval"):
            self.state.retrieval_churn_counter += 1
        elif signals.retrieval_delta:
            self.state.retrieval_churn_counter = 0
        churn = retrieval_churn(self._retrieval_attempts, self.contract.max_retrieval_churn)
        if churn.tripped and self.state.reasonfuse_enabled:
            self._trip(churn.reason or "RETRIEVAL_CHURN", fingerprint, completed=True)
        if (self.state.reasonfuse_enabled and not self.state.contained
                and self._stalled() and not verification
                and not self.state.verification_reserve_available):
            self._trip("NO_PROGRESS", fingerprint, completed=True)
        return Observation(
            signals={"evidence_delta": signals.evidence_delta, "world_state_delta": signals.world_state_delta,
                     "retrieval_delta": signals.retrieval_delta, "todo_delta": signals.todo_delta,
                     "postcondition_delta": signals.postcondition_delta,
                     "useful_recheck": useful},
            objective_progress=signals.objective_progress,
            trajectory_state=self.state.trajectory_state,
            progress_state=self.state.progress_state,
            fuse_reason=self.state.fuse_reason,
            executed=executed,
        )

    def set_outcome(self, outcome: dict[str, Any]) -> None:
        self.state.last_postcondition_result = outcome
        if outcome.get("outcome") == "OUTCOME_VERIFIED":
            self.state.pending_postcondition = None
            self.state.verification_reserve_available = False
            self.state.stall_counter = 0
            self.state.last_objective_progress_step = self.state.step_index
            self.state.progress_state = "PROGRESS"
            if self.state.progress_history:
                self.state.progress_history[-1] = True
                self._progress_history[-1] = True
        elif outcome.get("outcome") in {"POSTCONDITION_FAILED", "OUTCOME_UNKNOWN"} and self.state.reasonfuse_enabled:
            self._trip(outcome["outcome"], completed=True)
