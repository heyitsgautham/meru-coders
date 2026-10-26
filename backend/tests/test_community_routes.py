"""Community routes with the Supabase-backed model replaced by mocks.

The routes live in backend/api/community/ and share one CommunityModel
instance; these tests replace its methods to check what each route passes to
the model and how it answers.
"""

from unittest.mock import MagicMock

import jwt
import pytest

from backend.api import community


@pytest.fixture
def model(monkeypatch):
    """The shared CommunityModel instance with every method a test touches mocked."""
    names = [
        "get_posts",
        "get_post_by_id",
        "is_bookmarked",
        "create_post",
        "update_post",
        "delete_post",
        "toggle_like",
        "get_comments",
        "add_comment",
        "toggle_follow",
        "get_trending_posts",
        "search_posts",
        "report_content",
        "is_admin",
        "get_all_reports",
        "handle_report",
    ]
    mocks = {}
    for name in names:
        mocks[name] = MagicMock(return_value={"success": True})
        monkeypatch.setattr(community.community_model, name, mocks[name])
    mocks["is_bookmarked"].return_value = False
    mocks["is_admin"].return_value = False
    return mocks


def auth(app, user="kalidasa"):
    token = jwt.encode({"sub": user, "username": user}, app.config["SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_routes_are_registered_from_every_submodule(app):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules() if rule.endpoint.startswith("community.")}
    for name in ("upload_image", "get_posts", "add_comment", "toggle_follow", "take_report_action"):
        assert f"community.{name}" in endpoints
    assert len(endpoints) == 38


def test_feed_caps_the_page_size(client, model):
    model["get_posts"].return_value = {"success": True, "posts": []}
    resp = client.get("/api/community/posts?limit=500&offset=40")
    assert resp.status_code == 200
    model["get_posts"].assert_called_once_with(limit=100, offset=40, user_id=None)


def test_feed_marks_likes_and_bookmarks_for_a_signed_in_user(app, client, model):
    model["get_posts"].return_value = {"success": True, "posts": [{"id": "p1"}]}
    model["get_post_by_id"].return_value = {"success": True, "post": {"is_liked": True}}
    model["is_bookmarked"].return_value = True
    body = client.get("/api/community/posts", headers=auth(app)).get_json()
    assert body["posts"] == [{"id": "p1", "is_liked": True, "is_bookmarked": True}]


def test_creating_a_post_needs_a_login_and_content(app, client, model):
    assert client.post("/api/community/posts", json={"content": "x"}).status_code == 401
    resp = client.post("/api/community/posts", json={"content": ""}, headers=auth(app))
    assert resp.status_code == 400
    model["create_post"].assert_not_called()


def test_creating_a_post_with_a_verse_attaches_its_meter(app, client, model):
    resp = client.post(
        "/api/community/posts",
        json={"content": "Gita 1.1", "sanskrit_text": "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"},
        headers=auth(app),
    )
    assert resp.status_code == 201
    kwargs = model["create_post"].call_args.kwargs
    assert kwargs["user_id"] == "kalidasa"
    assert kwargs["meter_analysis"]["found"] is True
    assert "अनुष्टुभ्" in kwargs["meter_analysis"]["meter_name"]
    assert str(kwargs["meter_analysis"]["syllable_count"]) == "16"


def _edit(app, client, **body):
    resp = client.put("/api/community/posts/p1", json={"content": "Gita 1.1", **body}, headers=auth(app))
    assert resp.status_code == 200
    return resp


def test_editing_the_verse_stores_its_meter_in_the_shape_the_feed_reads(app, client, model):
    _edit(app, client, sanskrit_text="धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः")
    kwargs = model["update_post"].call_args.kwargs
    created = client.post(
        "/api/community/posts",
        json={"content": "Gita 1.1", "sanskrit_text": "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"},
        headers=auth(app),
    )
    assert created.status_code == 201
    assert kwargs["meter_analysis"] == model["create_post"].call_args.kwargs["meter_analysis"]
    assert str(kwargs["meter_analysis"]["syllable_count"]) == "16"


def test_editing_to_an_unmetered_verse_drops_the_old_meter(app, client, model):
    _edit(app, client, sanskrit_text="क")
    assert model["update_post"].call_args.kwargs["meter_analysis"] == {"found": False}


def test_clearing_the_verse_removes_it_and_its_meter(app, client, model):
    _edit(app, client, sanskrit_text="  ")
    kwargs = model["update_post"].call_args.kwargs
    assert kwargs["sanskrit_text"] == ""
    assert kwargs["meter_analysis"] == {"found": False}


def test_an_edit_without_the_verse_field_leaves_it_alone(app, client, model):
    _edit(app, client)
    kwargs = model["update_post"].call_args.kwargs
    assert kwargs["sanskrit_text"] is None
    assert kwargs["meter_analysis"] is None


def test_a_failed_model_call_is_a_400(app, client, model):
    model["delete_post"].return_value = {"success": False, "error": "Not your post"}
    resp = client.delete("/api/community/posts/p1", headers=auth(app))
    assert resp.status_code == 400
    model["delete_post"].assert_called_once_with("p1", "kalidasa")


def test_like_and_follow_toggle_for_the_signed_in_user(app, client, model):
    assert client.post("/api/community/posts/p1/like", headers=auth(app)).status_code == 200
    model["toggle_like"].assert_called_once()
    assert client.post("/api/community/users/u2/follow", headers=auth(app)).status_code == 200
    model["toggle_follow"].assert_called_once_with("kalidasa", "u2")


def test_comments_need_content(app, client, model):
    resp = client.post("/api/community/posts/p1/comments", json={}, headers=auth(app))
    assert resp.status_code == 400
    assert (
        client.post("/api/community/posts/p1/comments", json={"content": "सुन्दरम्"}, headers=auth(app)).status_code == 201
    )
    model["add_comment"].assert_called_once_with("p1", "kalidasa", "सुन्दरम्")


def test_search_needs_a_query(client, model):
    assert client.get("/api/community/search/posts?q=%20").status_code == 400
    assert client.get("/api/community/search/posts?q=gita").status_code == 200
    model["search_posts"].assert_called_once_with("gita", 20, 0)


def test_trending_feed_is_public(client, model):
    assert client.get("/api/community/feed/trending?limit=5").status_code == 200
    model["get_trending_posts"].assert_called_once_with(5, 0)


def test_reports_need_a_reason(app, client, model):
    assert client.post("/api/community/reports", json={"post_id": "p1"}, headers=auth(app)).status_code == 400
    model["report_content"].assert_not_called()


def test_moderation_is_admin_only(app, client, model):
    assert client.get("/api/community/admin/reports", headers=auth(app)).status_code == 403
    model["is_admin"].return_value = True
    assert client.get("/api/community/admin/reports?status=reviewed", headers=auth(app)).status_code == 200
    model["get_all_reports"].assert_called_once_with(status="reviewed", limit=50, offset=0)


def test_report_actions_are_checked(app, client, model):
    model["is_admin"].return_value = True
    resp = client.post("/api/community/admin/reports/r1/action", json={"action": "shout"}, headers=auth(app))
    assert resp.status_code == 400
    model["handle_report"].assert_not_called()
