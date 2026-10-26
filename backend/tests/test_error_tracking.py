"""Sentry stays off without a DSN, and tags reported errors with the request ID."""

import sentry_sdk
from flask import Flask
from sentry_sdk.transport import Transport

from backend.config import error_tracking
from backend.config.logging_config import init_request_logging


class RecordingTransport(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.events = []

    def capture_envelope(self, envelope):
        self.events.extend(item.payload.json for item in envelope.items if item.type == "event")


def test_no_dsn_means_no_client(monkeypatch):
    calls = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.append(kwargs))
    assert error_tracking.init_error_tracking("", "test") is False
    assert calls == []


def test_an_unhandled_error_reaches_sentry_with_its_request_id():
    transport = RecordingTransport()
    app = Flask(__name__)
    init_request_logging(app)

    @app.post("/boom")
    def boom():
        raise RuntimeError("verse parser exploded")

    try:
        started = error_tracking.init_error_tracking("https://key@o0.ingest.sentry.io/0", "test", transport=transport)
        response = app.test_client().post(
            "/boom", json={"text": "धर्मक्षेत्रे"}, headers={"X-Request-ID": "req-42", "Cookie": "session=secret"}
        )
        sentry_sdk.flush()
    finally:
        sentry_sdk.init()  # no DSN: switch the client back off for the other tests

    assert started is True
    assert response.status_code == 500
    [event] = transport.events
    assert event["tags"]["request_id"] == "req-42"
    assert event["environment"] == "test"
    assert event["exception"]["values"][-1]["value"] == "verse parser exploded"
    request = event.get("request", {})
    assert "धर्मक्षेत्रे" not in str(request.get("data", ""))
    assert "cookies" not in request and "Cookie" not in request.get("headers", {})
