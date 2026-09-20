"""Startup policy shared by the local and Hosted Agent compositions."""

from dataclasses import dataclass
import json
import os

from .core.contract import RunContract


@dataclass(frozen=True)
class RuntimeConfiguration:
    profile: str
    enabled: bool
    contract: RunContract


def runtime_configuration() -> RuntimeConfiguration:
    profile = os.environ.get("REASONFUSE_PROFILE", "runtime").strip().lower()
    if profile not in {"runtime", "evaluation"}:
        raise ValueError("REASONFUSE_PROFILE must be runtime or evaluation")
    enabled = os.environ.get("REASONFUSE_ENABLED", "true").strip().lower()
    if enabled not in {"true", "false"}:
        raise ValueError("REASONFUSE_ENABLED must be true or false")
    raw = json.loads(os.environ.get("REASONFUSE_CONTRACT_JSON") or "{}")
    if not isinstance(raw, dict):
        raise ValueError("REASONFUSE_CONTRACT_JSON must be an object")
    contract = RunContract.from_dict(raw)
    if profile == "runtime" and enabled != "true":
        raise ValueError("Disabling ReasonFuse requires REASONFUSE_PROFILE=evaluation")
    if profile == "runtime" and not contract.require_postcondition_for_side_effects:
        raise ValueError("The runtime profile requires side-effect postconditions")
    return RuntimeConfiguration(profile, enabled == "true", contract)
