"""Admin login credentials come from the environment, never from source."""

import pytest

from backend.auth import utils


@pytest.fixture
def admin_env(monkeypatch):
    monkeypatch.setattr(utils, "ADMIN_USERNAME", "site-admin")
    monkeypatch.setattr(utils, "ADMIN_PASSWORD", "correct horse battery")


def test_admin_login_disabled_without_password(monkeypatch):
    monkeypatch.setattr(utils, "ADMIN_PASSWORD", "")
    assert utils.check_admin_credentials(utils.ADMIN_USERNAME, "") is False
    assert utils.check_admin_credentials(utils.ADMIN_USERNAME, "anything") is False


def test_matching_credentials_pass(admin_env):
    assert utils.check_admin_credentials("site-admin", "correct horse battery") is True


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("site-admin", "wrong"),
        ("someone-else", "correct horse battery"),
        ("", ""),
    ],
)
def test_mismatched_credentials_fail(admin_env, username, password):
    assert utils.check_admin_credentials(username, password) is False
