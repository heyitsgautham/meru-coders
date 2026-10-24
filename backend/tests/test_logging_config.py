"""Structured logging and request IDs."""

import json
import logging

import pytest

from backend.config import logging_config


@pytest.fixture
def restore_root_logger():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


def _record(message="hello", **extra):
    record = logging.LogRecord("backend.test", logging.WARNING, __file__, 1, message, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_emits_one_parseable_object():
    line = logging_config.JsonFormatter().format(_record("नमः", request_id="abc", status=200))
    payload = json.loads(line)
    assert payload["message"] == "नमः"
    assert payload["level"] == "WARNING"
    assert payload["logger"] == "backend.test"
    assert payload["request_id"] == "abc"
    assert payload["status"] == 200
    assert payload["timestamp"].endswith("+00:00")
    assert "\n" not in line


def test_json_formatter_includes_exception():
    try:
        raise ValueError("bad verse")
    except ValueError:
        import sys

        record = _record("failed")
        record.exc_info = sys.exc_info()
    payload = json.loads(logging_config.JsonFormatter().format(record))
    assert "ValueError: bad verse" in payload["exception"]


@pytest.mark.parametrize(
    ("fmt", "formatter_type"), [("json", logging_config.JsonFormatter), ("text", logging.Formatter)]
)
def test_configure_logging_installs_one_handler(restore_root_logger, fmt, formatter_type):
    logging_config.configure_logging("debug", fmt)
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1
    assert type(root.handlers[0].formatter) is formatter_type


def test_unknown_level_falls_back_to_info(restore_root_logger):
    logging_config.configure_logging("LOUD", "text")
    assert logging.getLogger().level == logging.INFO


def test_request_id_filter_outside_a_request():
    record = _record()
    assert logging_config.RequestIdFilter().filter(record) is True
    assert record.request_id == "-"


def test_response_carries_a_generated_request_id(client):
    resp = client.get("/health")
    request_id = resp.headers[logging_config.REQUEST_ID_HEADER]
    assert len(request_id) == 32
    assert client.get("/health").headers[logging_config.REQUEST_ID_HEADER] != request_id


def test_incoming_request_id_is_echoed_and_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="backend.access"):
        resp = client.get("/health", headers={"X-Request-ID": "trace-123"})
    assert resp.headers["X-Request-ID"] == "trace-123"
    access = [r for r in caplog.records if r.name == "backend.access"]
    assert access[-1].path == "/health"
    assert access[-1].status == 200
    assert access[-1].duration_ms >= 0
