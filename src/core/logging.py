"""Logging configuration and JSON-structured log formatter for the service."""

import json
import logging
import sys
from typing import Any, Dict, Mapping

_STANDARD_LOG_RECORD_ATTRS: Mapping[str, None] = {
    # Core attributes
    "name": None,
    "msg": None,
    "args": None,
    "levelname": None,
    "levelno": None,
    "pathname": None,
    "filename": None,
    "module": None,
    "exc_info": None,
    "exc_text": None,
    "stack_info": None,
    "lineno": None,
    "funcName": None,
    "created": None,
    "msecs": None,
    "relativeCreated": None,
    "thread": None,
    "threadName": None,
    "process": None,
    "processName": None,
    # Derived / convenience attributes
    "message": None,
    "asctime": None,
}


class JSONFormatter(logging.Formatter):
    """Logging formatter that outputs records as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the given log record formatted as a JSON string."""
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include basic contextual information when available.
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        # Capture any extra fields that were attached via the `extra` parameter.
        # The logging module merges these into the record's __dict__, so we
        # collect keys that are not part of the standard LogRecord attributes.
        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_ATTRS:
                continue
            if key in log_record:
                # Do not allow extras to override the core fields above.
                continue
            if key.startswith("_"):
                # Skip private/internal attributes.
                continue
            log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure application-wide JSON logging.

    This should be called once at application startup.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Remove any existing handlers to avoid duplicate logs if reconfigured.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


# Module-level logger for convenience in core modules.
logger = logging.getLogger(__name__)
