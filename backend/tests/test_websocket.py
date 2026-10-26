"""The notification socket: who may connect, and what reaches them."""

import datetime

import jwt
import pytest

from backend import run
from backend.api import websocket
from backend.config import settings


def _token(user_id="u1", secret=None, minutes=5):
    payload = {
        "sub": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes),
    }
    return jwt.encode(payload, secret or settings.SECRET_KEY, algorithm="HS256")


@pytest.fixture
def socket_client(app):
    def connect(auth):
        return app.socketio.test_client(app, auth=auth)

    return connect


def test_a_valid_token_joins_the_user_room(socket_client):
    client = socket_client({"token": _token()})
    assert client.is_connected()
    assert client.get_received() == [
        {
            "name": "connected",
            "args": [{"message": "Connected to notification server", "user_id": "u1"}],
            "namespace": "/",
        }
    ]

    websocket.send_notification_to_user("u1", {"id": "n1", "type": "like"})
    websocket.emit_notification_count("u1", 3)
    websocket.send_notification_to_user("someone-else", {"id": "n2"})

    received = [(event["name"], event["args"][0]) for event in client.get_received()]
    assert received == [("new_notification", {"id": "n1", "type": "like"}), ("notification_count", {"unread_count": 3})]


@pytest.mark.parametrize(
    "auth",
    [None, {}, {"token": "not-a-jwt"}, {"token": _token(secret="x" * 32)}, {"token": _token(minutes=-1)}],
    ids=["no auth", "no token", "garbage", "wrong key", "expired"],
)
def test_the_server_refuses_bad_tokens(socket_client, auth):
    assert not socket_client(auth).is_connected()


def test_run_serves_through_socketio_when_the_app_has_it(monkeypatch):
    calls = []

    class FakeSocketIO:
        def run(self, app, **kwargs):
            calls.append(("socketio", kwargs["port"]))

    class FakeApp:
        socketio = FakeSocketIO()
        config = {"DEBUG": False}

        def run(self, **kwargs):
            calls.append(("flask", kwargs["port"]))

    monkeypatch.setattr(run, "create_app", lambda: FakeApp())
    monkeypatch.setenv("PORT", "5123")

    run.main()

    assert calls == [("socketio", 5123)]
