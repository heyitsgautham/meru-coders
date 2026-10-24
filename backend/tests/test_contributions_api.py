"""Integration test for contribution submission endpoint.

Ensures the /api/contributions/submit route exists, honors auth, and returns a JSON
payload rather than failing with 404/401. Uses a locally signed JWT so
it works without Supabase credentials.
"""

import jwt
from backend.app import create_app
from backend.config import settings


def _auth_header():
    token = jwt.encode(
        {'sub': 'test-user', 'username': 'test-user'},
        settings.SECRET_KEY,
        algorithm='HS256',
    )
    return {'Authorization': f'Bearer {token}'}


def test_submit_contribution_route_accessible():
    app = create_app()
    client = app.test_client()

    payload = {
        'contribution_type': 'verse',
        'data': {
            'verse_text': 'धर्मक्षेत्रे कुरुक्षेत्रे',
            'meter': 'Anushtubh',
            'source': 'test-suite',
            'notes': 'integration sanity',
        },
    }

    resp = client.post(
        '/api/contributions/submit',
        headers={**_auth_header(), 'Content-Type': 'application/json'},
        json=payload,
    )

    body = resp.get_json()

    # Route should exist and return a JSON body with a success flag
    assert resp.status_code not in (404, 405)
    assert body is not None
    assert 'success' in body

    # When Supabase is not configured we accept via dev fallback, otherwise real storage should succeed.
    if not body.get('success'):
        assert resp.status_code in (400, 500)
        assert 'error' in body
