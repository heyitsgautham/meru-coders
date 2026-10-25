"""Community comments and their replies."""

from flask import current_app, jsonify, request

from ...auth.middleware import require_auth
from . import community_bp, community_model

# ==================== COMMENTS ====================


@community_bp.route('/posts/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """
    Get comments for a post

    Query Parameters:
        limit: Number of comments (default 50)
        offset: Pagination offset (default 0)

    Returns:
        JSON with comments list
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)

        result = community_model.get_comments(post_id, limit, offset)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Get comments error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/posts/<post_id>/comments', methods=['POST'])
@require_auth
def add_comment(current_user, post_id):
    """
    Add a comment to a post

    Request JSON:
        {
            "content": "Comment text"
        }

    Returns:
        JSON with created comment data
    """
    try:
        data = request.get_json()

        if not data or not data.get('content'):
            return jsonify({'success': False, 'error': 'Content is required'}), 400

        content = data['content'].strip()
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        result = community_model.add_comment(post_id, user_id, content)

        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Add comment error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/comments/<comment_id>', methods=['DELETE'])
@require_auth
def delete_comment(current_user, comment_id):
    """
    Delete a comment (only by owner)

    Returns:
        JSON with success status
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')

        result = community_model.delete_comment(comment_id, user_id)

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        current_app.logger.error(f"Delete comment error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: COMMENT REPLIES ====================


@community_bp.route('/posts/<post_id>/comments/<comment_id>/replies', methods=['POST'])
@require_auth
def add_comment_reply(current_user, post_id, comment_id):
    """Add a reply to a comment"""
    try:
        data = request.get_json()
        if not data or not data.get('content'):
            return jsonify({'success': False, 'error': 'Content is required'}), 400

        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.add_comment_reply(
            post_id=post_id, user_id=user_id, content=data['content'].strip(), parent_id=comment_id
        )
        return jsonify(result), 201 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/comments/<comment_id>/replies', methods=['GET'])
def get_comment_replies(comment_id):
    """Get replies to a comment"""
    try:
        limit = min(request.args.get('limit', 20, type=int), 50)
        result = community_model.get_comment_replies(comment_id, limit)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
