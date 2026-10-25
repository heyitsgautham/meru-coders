"""Community posts: the feed, creating, editing and deleting posts, likes, and per-user post lists."""

from flask import current_app, jsonify, request

from ...auth.middleware import get_current_user, require_auth
from . import community_bp, community_model

# ==================== POSTS ====================


@community_bp.route('/posts', methods=['GET'])
def get_posts():
    """
    Get posts feed (chronological, newest first)

    Query Parameters:
        limit: Number of posts (default 20, max 100)
        offset: Pagination offset (default 0)
        user_id: Optional - filter by specific user

    Returns:
        JSON with posts list
    """
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        user_id = request.args.get('user_id', None)

        result = community_model.get_posts(limit=limit, offset=offset, user_id=user_id)

        # Check if current user has liked/bookmarked each post
        current_user = get_current_user()
        if current_user and result.get('posts'):
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
            for post in result['posts']:
                # Get like status for each post
                post_detail = community_model.get_post_by_id(post['id'], current_user_id)
                if post_detail.get('success'):
                    post['is_liked'] = post_detail['post'].get('is_liked', False)
                # Get bookmark status for each post
                post['is_bookmarked'] = community_model.is_bookmarked(post['id'], current_user_id)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get posts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/posts', methods=['POST'])
@require_auth
def create_post(current_user):
    """
    Create a new post

    Request JSON:
        {
            "content": "Post caption/text",
            "sanskrit_text": "Optional Sanskrit verse",
            "analyze_meter": true/false (default true if sanskrit_text provided)
        }

    Returns:
        JSON with created post data
    """
    try:
        data = request.get_json()

        if not data or not data.get('content'):
            return jsonify({'success': False, 'error': 'Content is required'}), 400

        content = data['content'].strip()
        sanskrit_text = data.get('sanskrit_text', '').strip() or None
        analyze_meter = data.get('analyze_meter', True)

        # Analyze meter if Sanskrit text is provided
        meter_analysis = None
        if sanskrit_text and analyze_meter:
            try:
                from ...config import settings
                from ...core import Chanda

                chanda = Chanda(data_path=str(settings.DATA_DIR))
                analysis_result = chanda.identify_line(sanskrit_text)

                if analysis_result.get('found'):
                    meter_analysis = {
                        'meter_name': analysis_result.get('display_chanda_primary', ''),
                        'lg_pattern': ''.join(analysis_result.get('display_lg', [])),
                        'syllable_count': analysis_result.get('display_length', 0),
                        'matra_count': analysis_result.get('display_matra', 0),
                        'gana_pattern': analysis_result.get('display_gana', ''),
                        'found': True,
                    }
                else:
                    meter_analysis = {'found': False}
            except Exception as e:
                current_app.logger.warning(f"Meter analysis failed: {e}")
                meter_analysis = {'found': False, 'error': str(e)}

        # Get user ID
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        # Get image URL if provided
        image_url = data.get('image_url')

        result = community_model.create_post(
            user_id=user_id,
            content=content,
            sanskrit_text=sanskrit_text,
            meter_analysis=meter_analysis,
            image_url=image_url,
        )

        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Create post error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """
    Get a single post by ID

    Returns:
        JSON with post data including like status for current user
    """
    try:
        current_user = get_current_user()
        current_user_id = None
        if current_user:
            current_user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        result = community_model.get_post_by_id(post_id, current_user_id)

        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get post error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/posts/<post_id>', methods=['DELETE'])
@require_auth
def delete_post(current_user, post_id):
    """
    Delete a post (only by owner)

    Returns:
        JSON with success status
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        result = community_model.delete_post(post_id, user_id)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Delete post error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== LIKES ====================


@community_bp.route('/posts/<post_id>/like', methods=['POST'])
@require_auth
def toggle_like(current_user, post_id):
    """
    Toggle like on a post (like if not liked, unlike if already liked)

    Returns:
        JSON with new like state
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        result = community_model.toggle_like(post_id, user_id)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Toggle like error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/posts/<post_id>/likes', methods=['GET'])
def get_post_likes(post_id):
    """
    Get users who liked a post

    Query Parameters:
        limit: Max users to return (default 50)

    Returns:
        JSON with users list
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)

        result = community_model.get_post_likes(post_id, limit)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get post likes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== USER ACTIVITY ====================


@community_bp.route('/users/<user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """
    Get posts by a specific user

    Query Parameters:
        limit: Number of posts (default 20)
        offset: Pagination offset (default 0)

    Returns:
        JSON with posts list
    """
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)

        result = community_model.get_user_posts(user_id, limit, offset)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get user posts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/users/<user_id>/liked', methods=['GET'])
def get_user_liked_posts(user_id):
    """
    Get posts liked by a user

    Query Parameters:
        limit: Number of posts (default 20)
        offset: Pagination offset (default 0)

    Returns:
        JSON with posts list
    """
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)

        result = community_model.get_liked_posts(user_id, limit, offset)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get user liked posts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== MY ACTIVITY (Current User) ====================


@community_bp.route('/me/posts', methods=['GET'])
@require_auth
def get_my_posts(current_user):
    """
    Get current user's posts

    Query Parameters:
        limit: Number of posts (default 20)
        offset: Pagination offset (default 0)

    Returns:
        JSON with posts list
    """
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        result = community_model.get_user_posts(user_id, limit, offset)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get my posts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/me/liked', methods=['GET'])
@require_auth
def get_my_liked_posts(current_user):
    """
    Get current user's liked posts

    Query Parameters:
        limit: Number of posts (default 20)
        offset: Pagination offset (default 0)

    Returns:
        JSON with posts list
    """
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        result = community_model.get_liked_posts(user_id, limit, offset)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get my liked posts error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: EDIT POST ====================


@community_bp.route('/posts/<post_id>', methods=['PUT', 'PATCH'])
@require_auth
def update_post(current_user, post_id):
    """
    Update a post (only by owner)

    Request JSON:
        {
            "content": "Updated content",
            "sanskrit_text": "Updated Sanskrit text",
            "analyze_meter": true/false,
            "image_url": "/api/community/uploads/..." or null to remove
        }
    """
    try:
        data = request.get_json()
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        content = data.get('content')
        sanskrit_text = data.get('sanskrit_text')
        analyze_meter = data.get('analyze_meter', True)

        # Handle image_url: check if key exists in request to differentiate
        # between "not updating" vs "removing the image"
        image_url = None
        update_image = False
        if 'image_url' in data:
            update_image = True
            image_url = data.get('image_url')  # Can be URL string or None to remove

        # Re-analyze meter if Sanskrit text changed
        meter_analysis = None
        if sanskrit_text and analyze_meter:
            try:
                from ...config import settings
                from ...core import Chanda

                chanda = Chanda(data_path=str(settings.DATA_DIR))
                analysis_result = chanda.identify_line(sanskrit_text)
                if analysis_result and analysis_result.get('found'):
                    meter_analysis = {
                        'found': True,
                        'meter_name': analysis_result.get('display_chanda_primary', ''),
                        'syllables': analysis_result.get('display_length', 0),
                        'pattern': ''.join(analysis_result.get('display_lg', [])),
                    }
            except Exception as e:
                current_app.logger.warning(f"Meter analysis failed: {e}")

        result = community_model.update_post(
            post_id=post_id,
            user_id=user_id,
            content=content,
            sanskrit_text=sanskrit_text,
            meter_analysis=meter_analysis,
            image_url=image_url,
            update_image=update_image,
        )

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Update post error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
