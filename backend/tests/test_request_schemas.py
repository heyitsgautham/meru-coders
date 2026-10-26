"""Request bodies are validated against the pydantic models in backend/api/schemas.py.

A malformed field gets a 400 with the field named in ``error`` and every problem
in ``details``, instead of reaching the handler and failing there.
"""

from unittest.mock import MagicMock

import jwt
import pytest
from pydantic import ValidationError

from backend.api import schemas
from backend.api.validation import describe


@pytest.fixture
def local_client(app):
    """No Supabase connection, as on a fresh clone."""
    app.supabase = None
    app.config["SUPABASE_CLIENT"] = None
    with app.test_client() as test_client:
        yield test_client


def bearer(app, sub="reviewer", is_admin=False):
    token = jwt.encode({"sub": sub, "username": sub, "is_admin": is_admin}, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


class TestModels:
    def test_identify_defaults(self):
        body = schemas.IdentifyTextRequest.model_validate({"text": "धर्म"})
        assert (body.identification_mode, body.enable_sandhi, body.effective_text_mode) == ("auto", False, "line")

    def test_identify_reads_the_legacy_mode_field(self):
        assert schemas.IdentifyTextRequest.model_validate({"text": "x", "mode": "verse"}).effective_text_mode == "verse"
        both = {"text": "x", "mode": "line", "text_mode": "verse"}
        assert schemas.IdentifyTextRequest.model_validate(both).effective_text_mode == "verse"

    @pytest.mark.parametrize(
        "body",
        [
            {"text": "x", "identification_mode": "prose"},
            {"text": "x", "enable_sandhi": "yes"},
            {"text": "x", "text_mode": "stanza"},
            {"text": 7},
        ],
    )
    def test_identify_rejects_bad_fields(self, body):
        with pytest.raises(ValidationError):
            schemas.IdentifyTextRequest.model_validate(body)

    def test_unknown_fields_are_ignored(self):
        assert schemas.DandakaRequest.model_validate({"text": "x", "debug": True}).text == "x"

    def test_search_bounds(self):
        assert schemas.SlokaSearchRequest.model_validate({"text": "x"}).limit == 10
        for body in ({"text": "x", "threshold": 1.5}, {"text": "x", "limit": 0}, {"text": "x", "limit": "many"}):
            with pytest.raises(ValidationError):
                schemas.SlokaSearchRequest.model_validate(body)

    def test_contribution_needs_a_known_type_and_an_object(self):
        ok = schemas.ContributionRequest.model_validate({"contribution_type": "verse", "data": {"verse_text": "x"}})
        assert ok.data == {"verse_text": "x"}
        for body in ({"contribution_type": "poem", "data": {}}, {"contribution_type": "verse", "data": "x"}, {}):
            with pytest.raises(ValidationError):
                schemas.ContributionRequest.model_validate(body)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        ({"loc": ("text",), "type": "missing", "msg": ""}, "Missing required field: text"),
        ({"loc": ("text",), "type": "string_type", "msg": ""}, "'text' must be a string"),
        (
            {"loc": ("text",), "type": "string_too_long", "msg": "", "ctx": {"max_length": 5}},
            "'text' is longer than 5 characters",
        ),
        ({"loc": ("enable_sandhi",), "type": "bool_type", "msg": ""}, "'enable_sandhi' must be true or false"),
        ({"loc": ("data",), "type": "dict_type", "msg": ""}, "'data' must be a JSON object"),
        (
            {"loc": ("limit",), "type": "greater_than_equal", "msg": "Input should be >= 1"},
            "'limit': Input should be >= 1",
        ),
    ],
)
def test_describe_names_the_field(error, message):
    assert describe(error) == message


def test_identify_rejects_an_unknown_mode_with_details(client):
    resp = client.post("/api/identify/text", json={"text": "धर्म", "identification_mode": "prose"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
    assert body["error"].startswith("'identification_mode' must be one of")
    assert body["details"] == [{"field": "identification_mode", "message": body["error"]}]


def test_identify_rejects_a_string_for_enable_sandhi(client):
    resp = client.post("/api/identify/text", json={"text": "धर्म", "enable_sandhi": "yes please"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "'enable_sandhi' must be true or false"


def test_identify_requires_text(client):
    resp = client.post("/api/identify/text", json={"identification_mode": "vedic"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Missing required field: text"


def test_search_rejects_a_threshold_above_one(client):
    resp = client.post("/api/sloka/search", json={"text": "धर्म", "threshold": 5})
    assert resp.status_code == 400
    assert resp.get_json()["details"][0]["field"] == "threshold"


@pytest.mark.parametrize("route", ["/api/auth/signup", "/api/auth/login", "/api/auth/admin-login"])
@pytest.mark.parametrize("username", [123, None, ["pingala"]])
def test_credentials_must_be_strings(local_client, route, username):
    """These used to reach .strip() and answer 500, or 401 for a list."""
    resp = local_client.post(route, json={"username": username, "password": "chandas123"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "'username' must be a string"


def test_overlong_username_is_rejected(local_client):
    resp = local_client.post("/api/auth/signup", json={"username": "a" * 65, "password": "chandas123"})
    assert resp.status_code == 400
    assert "longer than 64" in resp.get_json()["error"]


def test_contribution_data_must_be_an_object(app):
    with app.test_client() as client:
        resp = client.post(
            "/api/contributions/submit",
            headers=bearer(app),
            json={"contribution_type": "verse", "data": "धर्मक्षेत्रे"},
        )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "'data' must be a JSON object"


def test_contribution_type_must_be_known(app):
    with app.test_client() as client:
        resp = client.post(
            "/api/contributions/submit", headers=bearer(app), json={"contribution_type": "poem", "data": {}}
        )
    assert resp.status_code == 400
    assert resp.get_json()["details"][0]["field"] == "contribution_type"


def test_review_accepts_a_bare_post_but_not_bad_notes(app, monkeypatch):
    from backend.contributions import routes

    approve = MagicMock(return_value={"success": True})
    monkeypatch.setattr(routes.contribution_model, "approve_contribution", approve)
    headers = bearer(app, sub="admin", is_admin=True)
    with app.test_client() as client:
        bare = client.post("/api/contributions/admin/approve/123", headers=headers)
        bad = client.post("/api/contributions/admin/reject/123", headers=headers, json={"review_notes": 42})
    assert bare.status_code == 200
    approve.assert_called_once_with(contribution_id="123", admin_id="admin", review_notes="")
    assert bad.status_code == 400
    assert bad.get_json()["error"] == "'review_notes' must be a string"
