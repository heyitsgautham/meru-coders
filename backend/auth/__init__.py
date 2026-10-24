"""
Authentication module for Meru Coders - SIH 2025
Handles user authentication using Supabase built-in auth
"""

from .middleware import get_current_user, require_admin, require_auth
from .utils import is_admin_user

__all__ = ['require_auth', 'require_admin', 'get_current_user', 'is_admin_user']
