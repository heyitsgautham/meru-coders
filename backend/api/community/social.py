"""Community social graph: follows, feeds, bookmarks, search, notifications, profiles and blocks."""

from flask import current_app, jsonify, request

from ...auth.middleware import get_current_user, require_auth
from . import community_bp, community_model

# ==================== PHASE 2: FOLLOWS ====================


@community_bp.route('/users/<user_id>/follow', methods=['POST'])
@require_auth
def toggle_follow(current_user, user_id):
    """Toggle follow on a user"""
    try:
        follower_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.toggle_follow(follower_id, user_id)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    except Exception as e:
        current_app.logger.error(f"Toggle follow error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/users/<user_id>/followers', methods=['GET'])
def get_followers(user_id):
    """Get users who follow a specific user"""
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        result = community_model.get_followers(user_id, limit, offset)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/users/<user_id>/following', methods=['GET'])
def get_following(user_id):
    """Get users that a specific user follows"""
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        result = community_model.get_following(user_id, limit, offset)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/feed/following', methods=['GET'])
@require_auth
def get_following_feed(current_user):
    """Get posts from users the current user follows"""
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.get_following_feed(user_id, limit, offset)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: TRENDING ====================


@community_bp.route('/feed/trending', methods=['GET'])
def get_trending_feed():
    """Get trending posts based on engagement"""
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        result = community_model.get_trending_posts(limit, offset)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: BOOKMARKS ====================


@community_bp.route('/posts/<post_id>/bookmark', methods=['POST'])
@require_auth
def toggle_bookmark(current_user, post_id):
    """Toggle bookmark on a post"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.toggle_bookmark(post_id, user_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/me/bookmarks', methods=['GET'])
@require_auth
def get_bookmarked_posts(current_user):
    """Get current user's bookmarked posts"""
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.get_bookmarked_posts(user_id, limit, offset)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: SEARCH ====================


@community_bp.route('/search/posts', methods=['GET'])
def search_posts():
    """Search posts by content or Sanskrit text"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400

        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        result = community_model.search_posts(query, limit, offset)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/search/users', methods=['GET'])
def search_users():
    """Search users by username"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400

        limit = min(request.args.get('limit', 20, type=int), 50)
        result = community_model.search_users(query, limit)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: NOTIFICATIONS ====================


@community_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications(current_user):
    """Get current user's notifications"""
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.get_notifications(user_id, limit, unread_only)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@require_auth
def mark_notification_read(current_user, notification_id):
    """Mark a notification as read"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.mark_notification_read(notification_id, user_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/notifications/read-all', methods=['POST'])
@require_auth
def mark_all_notifications_read(current_user):
    """Mark all notifications as read"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.mark_all_notifications_read(user_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: USER PROFILES ====================


@community_bp.route('/users/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get a user's profile"""
    try:
        current_user = get_current_user()
        current_user_id = None
        if current_user:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.get_user_profile(user_id, current_user_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/me/profile', methods=['PUT', 'PATCH'])
@require_auth
def update_my_profile(current_user):
    """Update current user's profile"""
    try:
        data = request.get_json()
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.update_user_profile(
            user_id=user_id, bio=data.get('bio'), avatar_url=data.get('avatar_url')
        )
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/users/<user_id>/block', methods=['POST'])
@require_auth
def toggle_block(current_user, user_id):
    """Toggle block on a user"""
    try:
        blocker_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.toggle_block(blocker_id, user_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/me/blocked', methods=['GET'])
@require_auth
def get_blocked_users(current_user):
    """Get list of blocked users"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.get_blocked_users(user_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
