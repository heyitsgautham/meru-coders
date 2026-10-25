"""Malformed JSON bodies get a 400 with the API's error shape, not a 500."""

import pytest

from backend.api.validation import MAX_TEXT_LENGTH

TEXT_ROUTES = [
    ("/api/identify/text", "text"),
    ("/api/identify/dandaka", "text"),
    ("/api/sloka/search", "text"),
    ("/api/sloka/validate", "text"),
    ("/api/tts/generate", "text"),
    ("/api/chatbot/chat", "message"),
    ("/api/chatbot/analyze-meter", "text"),
]


@pytest.mark.parametrize(("route", "field"), TEXT_ROUTES)
def test_non_json_body_is_rejected(client, route, field):
    resp = client.post(route, data="not json", content_type="text/plain")
    assert resp.status_code == 400
    assert resp.get_json() == {"success": False, "error": "Request body must be a JSON object"}


@pytest.mark.parametrize(("route", "field"), TEXT_ROUTES)
def test_json_array_body_is_rejected(client, route, field):
    resp = client.post(route, json=["धर्म"])
    assert resp.status_code == 400


@pytest.mark.parametrize(("route", "field"), TEXT_ROUTES)
@pytest.mark.parametrize("value", [123, ["धर्म"], {"text": "धर्म"}])
def test_non_string_text_is_rejected(client, route, field, value):
    resp = client.post(route, json={field: value})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == f"'{field}' must be a string"


def test_oversized_text_is_rejected(client):
    resp = client.post("/api/identify/text", json={"text": "क" * (MAX_TEXT_LENGTH + 1)})
    assert resp.status_code == 400
    assert "longer than" in resp.get_json()["error"]


def test_valid_text_still_identifies(client):
    resp = client.post("/api/identify/text", json={"text": "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"})
    assert resp.status_code == 200
