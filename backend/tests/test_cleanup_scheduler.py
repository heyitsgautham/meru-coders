"""The upload cleanup scheduler starts only when CLEANUP_ENABLED allows it."""

from backend import app as app_module
from backend.config import settings


def test_disabled_by_the_test_environment():
    assert settings.CLEANUP_ENABLED is False
    assert app_module.create_app().scheduler is None


def test_enabled_app_runs_the_interval_job(monkeypatch):
    monkeypatch.setattr(settings, "CLEANUP_ENABLED", True)
    flask_app = app_module.create_app()
    try:
        job = flask_app.scheduler.get_job("upload_cleanup")
        assert flask_app.scheduler.running
        assert job.trigger.interval.total_seconds() == settings.CLEANUP_INTERVAL_MINUTES * 60
    finally:
        flask_app.scheduler.shutdown(wait=False)


def test_a_failing_scheduler_leaves_the_app_without_one(monkeypatch):
    class Broken:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("no threads")

    monkeypatch.setattr(settings, "CLEANUP_ENABLED", True)
    monkeypatch.setattr(app_module, "BackgroundScheduler", Broken)
    assert app_module.create_app().scheduler is None
