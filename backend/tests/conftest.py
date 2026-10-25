"""Shared fixtures for the backend test suite."""

import os

# No background cleanup thread in tests: every create_app() call would start one,
# and its exit hook would log after pytest has closed the output streams.
os.environ.setdefault("CLEANUP_ENABLED", "false")

import pytest  # noqa: E402

from backend.config import settings
from backend.core.chanda import Chanda


@pytest.fixture(scope="session")
def data_dir():
    """Absolute path to backend/data, independent of the working directory."""
    return settings.DATA_DIR


@pytest.fixture(scope="session")
def chanda(data_dir):
    """One Chanda engine for the whole run; loading the meter CSVs is slow."""
    return Chanda(data_path=str(data_dir))


@pytest.fixture
def app():
    from backend.app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    yield flask_app
    scheduler = getattr(flask_app, "scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=False)


@pytest.fixture
def client(app):
    with app.test_client() as test_client:
        yield test_client
