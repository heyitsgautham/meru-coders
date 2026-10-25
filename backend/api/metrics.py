"""
Prometheus metrics for the API, served at GET /metrics.

Requests are labelled by the matched route template (for example
/api/datasets/<dataset_id>), not the raw path, so label cardinality
stays bounded.
"""

import time

from flask import Flask, Response, g, request
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest

REGISTRY = CollectorRegistry()

REQUESTS = Counter(
    "meru_http_requests_total",
    "HTTP requests handled, by method, route and status code.",
    ["method", "route", "status"],
    registry=REGISTRY,
)
LATENCY = Histogram(
    "meru_http_request_duration_seconds",
    "Time spent handling a request, by method and route.",
    ["method", "route"],
    registry=REGISTRY,
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


def _route_label():
    return request.url_rule.rule if request.url_rule is not None else "unmatched"


def init_metrics(app: Flask) -> None:
    """Record every request and expose the registry at /metrics."""

    @app.before_request
    def _start_timer():
        g.metrics_started = time.perf_counter()

    @app.after_request
    def _record(response):
        route = _route_label()
        if route != "/metrics":
            REQUESTS.labels(request.method, route, str(response.status_code)).inc()
            started = g.get("metrics_started")
            if started is not None:
                LATENCY.labels(request.method, route).observe(time.perf_counter() - started)
        return response

    @app.route("/metrics", methods=["GET"])
    def metrics():
        return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)
