"""Small, bounded Azure Monitor log bridge for ReasonFuse decisions.

Only the ``reasonfuse.validation`` logger is connected to Application
Insights. This keeps model/framework logs out of the custom trace stream while
making the structured ReasonFuse decision fields queryable in AppTraces.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor


_PROVIDER: LoggerProvider | None = None


def configure_reasonfuse_log_exporter() -> tuple[LoggerProvider, LoggingHandler] | None:
    global _PROVIDER
    connection_string = (
        os.getenv("REASONFUSE_APPLICATIONINSIGHTS_CONNECTION_STRING")
        or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    )
    if not connection_string:
        return None

    # Hosted Agent runtimes may globally disable INFO logs while configuring
    # their own server logging.  The ReasonFuse logger is an explicit,
    # bounded audit channel and must remain enabled independently.
    logging.disable(logging.NOTSET)
    # The hosted platform may expose a malformed reserved variable even when
    # the project-specific value is valid.  This exporter version parses that
    # reserved variable before honoring an explicitly supplied connection
    # string, so remove it only for construction and restore it immediately.
    platform_connection_string = os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)
    try:
        exporter = AzureMonitorLogExporter.from_connection_string(connection_string)
    finally:
        if platform_connection_string is not None:
            os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = platform_connection_string

    provider = LoggerProvider()
    provider.add_log_record_processor(
        BatchLogRecordProcessor(
            exporter,
            schedule_delay_millis=1000,
            max_export_batch_size=64,
        )
    )
    handler = LoggingHandler(level=logging.INFO, logger_provider=provider)
    logger = logging.getLogger("reasonfuse.validation")
    logger.disabled = False
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    _PROVIDER = provider
    return provider, handler


def flush_reasonfuse_log_exporter() -> None:
    """Synchronously drain the bounded trace queue when validation asks for it."""

    if _PROVIDER is None or os.getenv("REASONFUSE_TRACE_FLUSH", "").lower() != "true":
        return
    _PROVIDER.force_flush(timeout_millis=5000)


def shutdown_reasonfuse_log_exporter(
    configured: tuple[LoggerProvider, LoggingHandler] | None,
) -> None:
    if not configured:
        return
    global _PROVIDER
    provider, handler = configured
    logger = logging.getLogger("reasonfuse.validation")
    logger.removeHandler(handler)
    provider.shutdown()
    _PROVIDER = None


def reasonfuse_log_extra(event: str, fields: dict[str, Any]) -> dict[str, Any]:
    """Return AppTraces-friendly scalar/JSON attributes for a validation event."""

    extra: dict[str, Any] = {"reasonfuse_event": event}
    for name, value in fields.items():
        if name == "attributes" and isinstance(value, dict):
            for attribute_name, attribute_value in value.items():
                normalized = attribute_name.replace("reasonfuse.", "", 1)
                extra[f"reasonfuse_{normalized.replace('.', '_')}"] = attribute_value
        elif isinstance(value, (str, int, float, bool)) or value is None:
            normalized = name.replace("reasonfuse.", "", 1)
            extra[f"reasonfuse_{normalized.replace('.', '_')}"] = value
    return extra
