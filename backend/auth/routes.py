"""
Authentication routes for Meru Coders.
Handles signup, login, logout using Supabase built-in auth.
"""

import os
from email.utils import parseaddr

from flask import Blueprint, request, jsonify, current_app
from supabase import Client
import jwt
import time
from .utils import create_user_profile, get_user_profile, ADMIN_USERNAME, ADMIN_PASSWORD

EMAIL_DOMAIN = os.environ.get("AUTH_EMAIL_DOMAIN", "merucoders.app")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
from .middleware import get_current_user


def _generate_email(username: str) -> str:
    """Generate a synthetic email for Supabase auth (username-based auth)."""
    return f"{username}@{EMAIL_DOMAIN}"


def _redact(token: str | None, keep: int = 4) -> str:
    """Redact sensitive tokens for logging."""
    if not token:
        return "<empty>"
    prefix = token[:keep]
    suffix = token[-keep:] if len(token) > keep else ""
    return f"{prefix}...{suffix} (len={len(token)})"


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Register a new user with username and password.
    Password is securely hashed using bcrypt.
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Missing credentials',
                'message': 'Username and password are required'
            }), 400
        
        # Validate username
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': 'Invalid username',
                'message': 'Username must be at least 3 characters long'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Invalid password',
                'message': 'Password must be at least 6 characters long'
            }), 400
        
        # Check if admin username (reserved)
        if username == ADMIN_USERNAME:
            return jsonify({
                'success': False,
                'error': 'Username reserved',
                'message': 'This username is reserved for admin use'
            }), 400
        
        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        
        # Check if username already exists
        existing = supabase.table('users').select('id').eq('username', username).execute()
        if existing.data:
            return jsonify({
                'success': False,
                'error': 'Username taken',
                'message': 'This username is already registered'
            }), 409

        # Hash password with bcrypt
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user in database
        import uuid
        user_id = str(uuid.uuid4())
        
        user_data = {
            'id': user_id,
            'username': username,
            'password_hash': password_hash,
            'is_admin': False,
            'created_at': 'now()'
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': 'Signup failed',
                'message': 'Could not create user account'
            }), 500
        
        # Generate JWT token
        import jwt
        import time
        from backend.config import settings
        
        payload = {
            'sub': user_id,
            'username': username,
            'is_admin': False,
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600 * 24  # 24 hours
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {
                'id': user_id,
                'username': username
            },
            'session': {
                'access_token': token,
                'refresh_token': None
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Signup error: {e}")
        return jsonify({
            'success': False,
            'error': 'Signup failed',
            'message': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with username and password.
    Verifies password hash with bcrypt.
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Missing credentials',
                'message': 'Username and password are required'
            }), 400
        
        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        
        # Fallback for local/dev when Supabase is not configured
        if supabase is None:
            import uuid
            user_id = f"local-{username}" or str(uuid.uuid4())
            payload = {
                'sub': user_id,
                'username': username,
                'is_admin': False,
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600 * 24
            }
            token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({
                'success': True,
                'message': 'Login successful (local dev fallback)',
                'user': {
                    'id': user_id,
                    'username': username,
                    'is_admin': False
                },
                'session': {
                    'access_token': token,
                    'refresh_token': None
                }
            }), 200

        # Look up user by username
        result = supabase.table('users').select('*').eq('username', username).execute()
        
        if not result.data or len(result.data) == 0:
            return jsonify({
                'success': False,
                'error': 'Login failed',
                'message': 'Invalid username or password'
            }), 401

        user = result.data[0]
        
        # Verify password with bcrypt
        import bcrypt
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({
                'success': False,
                'error': 'Login failed',
                'message': 'Invalid username or password'
            }), 401
        
        # Generate JWT token
        import jwt
        import time
        from backend.config import settings
        
        payload = {
            'sub': user['id'],
            'username': user['username'],
            'is_admin': user.get('is_admin', False),
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600 * 24  # 24 hours
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'is_admin': user.get('is_admin', False)
            },
            'session': {
                'access_token': token,
                'refresh_token': None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed',
            'message': 'Invalid username or password'
        }), 401


@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    """
    Admin login with hardcoded credentials.
    Returns a local JWT (no email) to avoid Supabase email validation issues.
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Verify admin credentials
        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials',
                'message': 'Invalid admin username or password'
            }), 401
        
        # Issue a local JWT to bypass Supabase email constraints
        # Use a fixed UUID-like subject so downstream Supabase UUID columns accept it
        payload = {
            'sub': '00000000-0000-0000-0000-000000000001',
            'username': ADMIN_USERNAME,
            'is_admin': True,
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600 * 24  # 24 hours
        }
        token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            'success': True,
            'message': 'Admin login successful',
            'user': {
                'id': ADMIN_USERNAME,
                'username': ADMIN_USERNAME,
                'is_admin': True
            },
            'session': {
                'access_token': token,
                'refresh_token': None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Admin login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Admin login failed',
            'message': str(e)
        }), 500


@auth_bp.route('/oauth/start', methods=['POST'])
def oauth_start():
    """Begin an OAuth flow (currently Google)."""
    try:
        data = request.get_json() or {}
        provider = data.get('provider', 'google')
        redirect_to = data.get('redirect_to') or f"{FRONTEND_URL}/oauth/callback"

        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        current_app.logger.info(
            "OAuth start request: provider=%s redirect_to=%s has_supabase=%s origin=%s",
            provider,
            redirect_to,
            bool(supabase),
            request.headers.get('Origin')
        )

        oauth_response = supabase.auth.sign_in_with_oauth({
            'provider': provider,
            'options': {
                'redirect_to': redirect_to
            }
        })

        url = getattr(oauth_response, 'url', None)
        if url is None and isinstance(oauth_response, dict):
            url = oauth_response.get('url')

        current_app.logger.info(
            "OAuth start response: url=%s response_type=%s",
            url,
            type(oauth_response).__name__
        )

        if not url:
            return jsonify({
                'success': False,
                'error': 'OAuth start failed',
                'message': 'Provider did not return a redirect URL'
            }), 500

        return jsonify({
            'success': True,
            'url': url
        }), 200

    except Exception as e:
        current_app.logger.error(f"OAuth start error: {e}")
        return jsonify({
            'success': False,
            'error': 'OAuth start failed',
            'message': str(e)
        }), 500


@auth_bp.route('/oauth/exchange', methods=['POST'])
def oauth_exchange():
    """Exchange a Supabase access token from OAuth for a local session."""
    try:
        data = request.get_json() or {}
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')

        current_app.logger.info(
            "OAuth exchange request: access=%s refresh=%s origin=%s",
            _redact(access_token),
            _redact(refresh_token),
            request.headers.get('Origin')
        )

        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Missing token',
                'message': 'Access token is required'
            }), 400

        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        user_response = supabase.auth.get_user(access_token)
        supabase_user = getattr(user_response, 'user', None)

        current_app.logger.info(
            "OAuth exchange Supabase response: has_user=%s response_type=%s",
            bool(supabase_user),
            type(user_response).__name__
        )

        if not supabase_user:
            return jsonify({
                'success': False,
                'error': 'Invalid token',
                'message': 'Could not validate OAuth session'
            }), 401

        email = supabase_user.email
        username = supabase_user.user_metadata.get('preferred_username') if supabase_user.user_metadata else None
        if not username:
            username = supabase_user.user_metadata.get('user_name') if supabase_user.user_metadata else None
        if not username:
            username = (email.split('@')[0] if email and '@' in email else supabase_user.id)

        profile = get_user_profile(supabase_user.id)
        current_app.logger.info(
            "OAuth exchange profile lookup: user_id=%s found=%s",
            supabase_user.id,
            bool(profile)
        )
        if not profile:
            create_user_profile(
                user_id=supabase_user.id,
                username=username,
                email=email,
                is_admin=False
            )
            profile = get_user_profile(supabase_user.id)
            current_app.logger.info(
                "OAuth exchange profile created: user_id=%s success=%s",
                supabase_user.id,
                bool(profile)
            )

        return jsonify({
            'success': True,
            'message': 'OAuth login successful',
            'user': {
                'id': supabase_user.id,
                'username': profile.get('username') if profile else username,
                'email': profile.get('email') if profile else email,
                'is_admin': profile.get('is_admin', False) if profile else False
            },
            'session': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"OAuth exchange error: {e}")
        return jsonify({
            'success': False,
            'error': 'OAuth exchange failed',
            'message': str(e)
        }), 500


@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """
    Get current user profile.
    Requires authentication.
    """
    user = get_current_user()
    
    if not user:
        return jsonify({
            'success': False,
            'error': 'Not authenticated',
            'message': 'Please log in to view profile'
        }), 401
    
    profile = get_user_profile(user.id)
    
    if not profile:
        return jsonify({
            'success': False,
            'error': 'Profile not found',
            'message': 'User profile could not be retrieved'
        }), 404
    
    return jsonify({
        'success': True,
        'user': profile
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout current user.
    Invalidates Supabase session.
    """
    user = get_current_user()
    
    if user:
        try:
            supabase: Client = current_app.config['SUPABASE_CLIENT']
            supabase.auth.sign_out()
        except Exception as e:
            current_app.logger.error(f"Logout error: {e}")
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200
