"""Optional error reporting to Sentry.

Nothing is sent unless SENTRY_DSN is set. When it is, unhandled exceptions and
ERROR log records reach Sentry tagged with the request ID that the API returns in
X-Request-ID, so a user's report can be matched to its event.
"""

import sentry_sdk
from flask import g, has_request_context
from sentry_sdk.integrations.flask import FlaskIntegration


def _tag_request_id(event, _hint):
    if has_request_context() and g.get("request_id"):
        event.setdefault("tags", {})["request_id"] = g.request_id
    return event


def init_error_tracking(dsn: str, environment: str, traces_sample_rate: float = 0.0, **options) -> bool:
    """Start the Sentry client when a DSN is configured. Returns whether it started."""
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[FlaskIntegration()],
        traces_sample_rate=traces_sample_rate,
        # Verses, prompts, cookies and client IPs stay out of reports.
        send_default_pii=False,
        max_request_body_size="never",
        before_send=_tag_request_id,
        **options,
    )
    return True
