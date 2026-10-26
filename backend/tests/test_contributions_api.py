"""The contribution routes without Supabase, as on a fresh clone."""

import jwt
import pytest

from backend.config import settings
from backend.contributions import routes
from backend.models.contribution import NOT_CONFIGURED

VERSE = {
    'contribution_type': 'verse',
    'data': {'verse_text': 'धर्मक्षेत्रे कुरुक्षेत्रे', 'meter': 'Anushtubh', 'source': 'test-suite'},
}


def _auth_header(**claims):
    token = jwt.encode({'sub': 'test-user', 'username': 'test-user', **claims}, settings.SECRET_KEY, algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def no_storage(app, monkeypatch):
    app.supabase = None
    app.config['SUPABASE_CLIENT'] = None
    monkeypatch.setattr(routes.contribution_model, 'supabase', None)
    with app.test_client() as client:
        yield client


def test_a_submission_with_nowhere_to_go_is_refused_not_dropped(no_storage):
    resp = no_storage.post('/api/contributions/submit', headers=_auth_header(), json=VERSE)
    assert resp.status_code == 400
    assert resp.get_json() == {'success': False, 'error': NOT_CONFIGURED}


@pytest.mark.parametrize('action', ['approve', 'reject'])
def test_a_review_with_nowhere_to_go_is_refused(no_storage, action):
    resp = no_storage.post(f'/api/contributions/admin/{action}/c1', headers=_auth_header(is_admin=True))
    assert resp.status_code == 400
    assert resp.get_json()['error'] == NOT_CONFIGURED


def test_submitting_needs_a_login(no_storage):
    assert no_storage.post('/api/contributions/submit', json=VERSE).status_code == 401
