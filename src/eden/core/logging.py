from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from eden.core.config import settings


class JsonFormatter(logging.Formatter):
    """One JSON object per line; `severity` is the field Cloud Logging reads."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Avoid duplicate handlers if hot reload
    root.handlers = [handler]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
