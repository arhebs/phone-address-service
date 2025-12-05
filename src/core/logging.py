"""Logging configuration and JSON-structured log formatter for the service."""

import json
import logging
import sys
from typing import Any, Dict


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
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_record.update(record.extra)

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
