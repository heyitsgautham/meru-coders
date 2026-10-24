"""
Logging setup for the API.

LOG_FORMAT=json writes one JSON object per line for log collectors such as
Cloud Logging; LOG_FORMAT=text (the default) keeps the readable format.
Every record carries the current request ID, which the API also returns in
the X-Request-ID response header.
"""

import json
import logging
import time
import uuid
from datetime import UTC, datetime

from flask import Flask, g, has_request_context, request

REQUEST_ID_HEADER = "X-Request-ID"
TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"


class RequestIdFilter(logging.Filter):
    """Attach the current request ID, or "-" outside a request, to each record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = g.get("request_id", "-") if has_request_context() else "-"
        return True


class JsonFormatter(logging.Formatter):
    """Format a record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for key in ("method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Replace the root handlers with one stream handler in the chosen format."""
    resolved = logging.getLevelName(level.upper())
    if not isinstance(resolved, int):
        resolved = logging.INFO

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter() if fmt.lower() == "json" else logging.Formatter(TEXT_FORMAT))

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(resolved)


def init_request_logging(app: Flask) -> None:
    """Assign a request ID to every request and log one access line per response."""
    access_logger = logging.getLogger("backend.access")

    @app.before_request
    def _start_request():
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        g.request_id = incoming[:64] if incoming else uuid.uuid4().hex
        g.request_started = time.perf_counter()

    @app.after_request
    def _finish_request(response):
        response.headers[REQUEST_ID_HEADER] = g.get("request_id", "-")
        started = g.get("request_started")
        duration_ms = round((time.perf_counter() - started) * 1000, 1) if started else None
        access_logger.info(
            "%s %s %s",
            request.method,
            request.path,
            response.status_code,
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
