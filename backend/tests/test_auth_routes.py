"""Auth endpoints when Supabase is not configured (local development)."""

import jwt
import pytest

from backend.auth import utils


@pytest.fixture
def local_client(app):
    """A client whose app has no Supabase connection, as on a fresh clone."""
    app.supabase = None
    app.config["SUPABASE_CLIENT"] = None
    with app.test_client() as test_client:
        yield test_client


def _decode(app, token):
    return jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])


def test_login_falls_back_to_a_local_token(app, local_client):
    resp = local_client.post("/api/auth/login", json={"username": "pingala", "password": "chandas123"})

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["user"] == {"id": "local-pingala", "username": "pingala", "is_admin": False}
    claims = _decode(app, body["session"]["access_token"])
    assert claims["sub"] == "local-pingala"
    assert claims["exp"] - claims["iat"] == 24 * 3600


@pytest.mark.parametrize("payload", [{}, {"username": "pingala"}, {"password": "chandas123"}])
def test_login_requires_both_fields(local_client, payload):
    resp = local_client.post("/api/auth/login", json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Missing credentials"


def test_login_without_json_body_is_a_400(local_client):
    resp = local_client.post("/api/auth/login", data="not json", content_type="text/plain")
    assert resp.status_code == 400


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"username": "ab", "password": "chandas123"}, "Invalid username"),
        ({"username": "pingala", "password": "short"}, "Invalid password"),
    ],
)
def test_signup_validates_input(local_client, payload, error):
    resp = local_client.post("/api/auth/signup", json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == error


def test_signup_rejects_the_admin_username(local_client):
    resp = local_client.post("/api/auth/signup", json={"username": utils.ADMIN_USERNAME, "password": "chandas123"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Username reserved"


def test_signup_without_supabase_is_unavailable(local_client):
    resp = local_client.post("/api/auth/signup", json={"username": "pingala", "password": "chandas123"})
    assert resp.status_code == 503
    assert resp.get_json()["error"] == "Signup unavailable"


def test_admin_login_issues_an_admin_token(app, local_client, monkeypatch):
    monkeypatch.setattr(utils, "ADMIN_PASSWORD", "correct horse battery")
    resp = local_client.post(
        "/api/auth/admin-login",
        json={"username": utils.ADMIN_USERNAME, "password": "correct horse battery"},
    )

    assert resp.status_code == 200
    claims = _decode(app, resp.get_json()["session"]["access_token"])
    assert claims["is_admin"] is True


def test_admin_login_disabled_without_password(local_client, monkeypatch):
    monkeypatch.setattr(utils, "ADMIN_PASSWORD", "")
    resp = local_client.post("/api/auth/admin-login", json={"username": utils.ADMIN_USERNAME, "password": ""})
    assert resp.status_code == 401
