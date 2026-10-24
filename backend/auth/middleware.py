"""
Authentication middleware for Meru Coders.
Provides decorators for protecting routes with Supabase JWT verification.
"""

from functools import wraps

import jwt
from flask import current_app, jsonify, request
from supabase import Client


def get_current_user():
    """
    Extract and verify user from Supabase JWT token in Authorization header.
    Returns user data or None if invalid/missing token.
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]

    # Try Supabase JWT first
    try:
        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        user_response = supabase.auth.get_user(token)
        if user_response and user_response.user:
            return user_response.user
    except Exception as e:
        current_app.logger.error(f"Token verification via Supabase failed: {e}")

    # Fallback: local JWT (for admin)
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return {
            'id': payload.get('sub'),
            'email': None,
            'user_metadata': {
                'username': payload.get('username'),
                'is_admin': payload.get('is_admin'),
            }
        }
    except Exception as e:
        current_app.logger.error(f"Local token verification failed: {e}")
        return None


def require_auth(f):
    """
    Decorator to require authentication for a route.
    Verifies Supabase JWT token and attaches user to request.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in to access this resource'
            }), 401

        # Attach user to request for use in route
        request.current_user = user
        return f(user, *args, **kwargs)

    return decorated_function


def require_admin(f):
    """
    Decorator to require admin authentication for a route.
    Checks if user has admin privileges (username = admin-erase-sure).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        if not user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in to access this resource'
            }), 401

        # If token came from local admin login, trust is_admin flag in metadata
        meta_admin = None
        if isinstance(user, dict):
            meta_admin = user.get('user_metadata', {}).get('is_admin')
        else:
            meta_admin = getattr(user, 'user_metadata', {}).get('is_admin') if hasattr(user, 'user_metadata') else None
        if meta_admin:
            request.current_user = user
            username = user.get('id') if isinstance(user, dict) else getattr(user, 'id', '')
            request.admin_data = {'is_admin': True, 'username': username}
            return f(user, *args, **kwargs)

        # Otherwise check Supabase table
        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        try:
            result = supabase.table('users').select('is_admin, username').eq('id', user.id).single().execute()
            if not result.data or not result.data.get('is_admin'):
                return jsonify({
                    'success': False,
                    'error': 'Admin access required',
                    'message': 'You do not have permission to access this resource'
                }), 403

            request.current_user = user
            request.admin_data = result.data
            return f(user, *args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"Admin verification failed: {e}")
            return jsonify({
                'success': False,
                'error': 'Authorization failed',
                'message': 'Could not verify admin status'
            }), 500

    return decorated_function
