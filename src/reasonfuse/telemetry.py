"""Small structured runtime events, independent of synthetic validation state."""

import json
import logging
from datetime import datetime, timezone

from agent_framework import Content
from opentelemetry import trace


def json_value(value):
    if isinstance(value, Content):
        return {"type": value.type, "text": value.text}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return str(value)


def emit(event: str, **fields) -> None:
    span = trace.get_current_span().get_span_context()
    logging.getLogger("reasonfuse.runtime").info(json.dumps({
        "event": event,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "trace_id": format(span.trace_id, "032x") if span.is_valid else None,
        **fields,
    }, default=json_value, sort_keys=True))
