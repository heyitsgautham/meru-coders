"""Prometheus metrics at /metrics."""

from backend.api.metrics import REGISTRY


def _count(method, route, status):
    value = REGISTRY.get_sample_value("meru_http_requests_total", {"method": method, "route": route, "status": status})
    return value or 0.0


def test_metrics_endpoint_serves_prometheus_text(client):
    client.get("/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert resp.mimetype == "text/plain"
    body = resp.get_data(as_text=True)
    assert "# TYPE meru_http_requests_total counter" in body
    assert "meru_http_request_duration_seconds_bucket" in body


def test_requests_are_counted_by_route_template(client):
    before = _count("GET", "/api/datasets/<dataset_id>", "404")
    client.get("/api/datasets/no-such-dataset")
    client.get("/api/datasets/another-missing-one")
    assert _count("GET", "/api/datasets/<dataset_id>", "404") == before + 2


def test_unmatched_paths_share_one_label(client):
    before = _count("GET", "unmatched", "404")
    client.get("/no/such/page")
    assert _count("GET", "unmatched", "404") == before + 1


def test_metrics_scrapes_are_not_counted(client):
    client.get("/metrics")
    assert _count("GET", "/metrics", "200") == 0
