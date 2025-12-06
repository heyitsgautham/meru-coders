"""
Authentication utility functions.
"""

from flask import current_app
from supabase import Client


ADMIN_USERNAME = "admin-erase-sure"
ADMIN_PASSWORD = "Pazz!$79UNO"


def is_admin_user(user_id: str) -> bool:
    """
    Check if a user ID belongs to an admin user.
    
    Args:
        user_id: Supabase user ID
        
    Returns:
        True if user is admin, False otherwise
    """
    try:
        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        result = supabase.table('users').select('is_admin').eq('id', user_id).single().execute()
        
        return bool(result.data and result.data.get('is_admin'))
    except Exception as e:
        current_app.logger.error(f"Admin check failed: {e}")
        return False


def get_user_profile(user_id: str) -> dict:
    """
    Get user profile data from database.
    
    Args:
        user_id: Supabase user ID
        
    Returns:
        User profile dict or None if not found
    """
    try:
        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        result = supabase.table('users').select('*').eq('id', user_id).single().execute()
        
        if result.data:
            # Remove password_hash from response
            user_data = result.data.copy()
            user_data.pop('password_hash', None)
            return user_data
        return None
    except Exception as e:
        current_app.logger.error(f"Get user profile failed: {e}")
        return None


def create_user_profile(user_id: str, username: str, email: str = None, is_admin: bool = False) -> bool:
    """
    Create a user profile in the users table after Supabase auth signup.
    
    Args:
        user_id: Supabase auth user ID
        username: Chosen username
        email: Optional email
        is_admin: Whether user is admin
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase: Client = current_app.config.get('SUPABASE_CLIENT') or current_app.supabase
        
        user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'is_admin': is_admin
        }
        
        result = supabase.table('users').insert(user_data).execute()
        return bool(result.data)
    except Exception as e:
        current_app.logger.error(f"Create user profile failed: {e}")
        return False
