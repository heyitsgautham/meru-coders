"""Routes share one Chanda engine instead of loading the meter tables on every request."""

from unittest.mock import MagicMock

import jwt

from backend.api import community
from backend.core import engine


class StubEngine:
    def __init__(self):
        self.lines = []

    def identify_line(self, text):
        self.lines.append(text)
        return {"found": True, "display_chanda_primary": "stub-meter", "display_lg": ["G"], "display_length": 1}


def test_inside_an_app_the_engine_is_the_apps(app):
    with app.app_context():
        assert engine.get_engine() is app.chanda


def test_outside_an_app_one_engine_is_cached(chanda):
    first = engine.get_engine()
    assert first is engine.get_engine()
    assert first.identify_line("धर्मक्षेत्रे कुरुक्षेत्रे")["found"] == chanda.identify_line("धर्मक्षेत्रे कुरुक्षेत्रे")["found"]


def test_community_posts_use_the_app_engine(app, monkeypatch):
    stub = StubEngine()
    app.chanda = stub
    create = MagicMock(return_value={"success": True})
    monkeypatch.setattr(community.community_model, "create_post", create)
    token = jwt.encode({"sub": "u1"}, app.config["SECRET_KEY"], algorithm="HS256")
    with app.test_client() as client:
        resp = client.post(
            "/api/community/posts",
            json={"content": "x", "sanskrit_text": "धर्मक्षेत्रे"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 201
    assert stub.lines == ["धर्मक्षेत्रे"]
    assert create.call_args.kwargs["meter_analysis"]["meter_name"] == "stub-meter"


def test_chatbot_meter_analysis_uses_the_app_engine(app, monkeypatch):
    from backend.api import chatbot_meter

    stub = StubEngine()
    stub.identify_from_text = MagicMock(return_value={"result": {"line": [], "verse": []}})
    app.chanda = stub
    with app.app_context():
        assert engine.get_engine() is stub
        chatbot_meter.analyze_meter_agentic("धर्मक्षेत्रे कुरुक्षेत्रे\nसमवेता युयुत्सवः")
    stub.identify_from_text.assert_called_once()
    assert stub.identify_from_text.call_args.kwargs == {"verse": True, "mode": "auto"}
