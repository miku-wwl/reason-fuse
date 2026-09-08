"""Versioned canonical tool-call fingerprints."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

FINGERPRINT_SCHEMA = "reasonfuse-fingerprint-v1"


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not valid tool arguments")
        return value
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON tool argument keys must be strings")
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        # Arrays can be order-sensitive tool arguments; preserve their order.
        return [_normalize(item) for item in value]
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump(mode="json"))
    raise TypeError(f"unsupported tool argument type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(_normalize(value), ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def tool_fingerprint(tool_name: str, arguments: Any) -> str:
    if not isinstance(tool_name, str) or not tool_name:
        raise ValueError("tool_name is required")
    payload = tool_name + canonical_json(arguments)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
