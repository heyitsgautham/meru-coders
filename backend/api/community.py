"""
Community API Routes
Twitter-like social platform for Sanskrit enthusiasts
Handles posts, likes, comments, and image uploads
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from ..auth.middleware import require_auth, get_current_user
from ..models.community import CommunityModel
from ..config.settings import settings

community_bp = Blueprint('community', __name__)
community_model = CommunityModel()

# Image upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== SERVE UPLOADED FILES ====================

@community_bp.route('/uploads/<path:filepath>', methods=['GET'])
def serve_upload(filepath):
    """
    Serve uploaded files (images, etc.)
    This handles URLs like /api/community/uploads/community/{user_id}/{filename}
    """
    try:
        # The filepath will be like: community/{user_id}/{filename}
        upload_dir = settings.UPLOADS_DIR
        return send_from_directory(upload_dir, filepath)
    except Exception as e:
        current_app.logger.error(f"Error serving upload: {e}")
        return jsonify({'error': 'File not found'}), 404


# ==================== IMAGE UPLOAD ====================

@community_bp.route('/upload/image', methods=['POST'])
@require_auth
def upload_image(current_user):
    """
    Upload an image for a post
    
    Request:
        multipart/form-data with 'image' field
    
    Returns:
        JSON with image URL
    """
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_IMAGE_SIZE:
            return jsonify({
                'success': False, 
                'error': 'Image too large. Maximum size is 5MB'
            }), 400
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        secure_name = secure_filename(filename)
        
        # Try to upload to Supabase Storage if available
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        
        if community_model.supabase:
            try:
                # Upload to Supabase Storage
                file_path = f"posts/{user_id}/{secure_name}"
                file_content = file.read()
                
                result = community_model.supabase.storage.from_('community-images').upload(
                    file_path,
                    file_content,
                    {'content-type': file.content_type}
                )
                
                # Get public URL
                public_url = community_model.supabase.storage.from_('community-images').get_public_url(file_path)
                
                return jsonify({
                    'success': True,
                    'url': public_url
                }), 200
                
            except Exception as storage_error:
                current_app.logger.warning(f"Supabase storage error, falling back to local: {storage_error}")
                # Reset file pointer for local storage fallback
                file.seek(0)
        
        # Fallback to local storage
        upload_dir = settings.UPLOADS_DIR / 'community' / user_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / secure_name
        # Ensure file pointer is at beginning before saving
        file.seek(0)
        file.save(str(file_path))
        
        # Return URL that works with our serve_upload route
        # The route is at /api/community/uploads/<path>
        relative_url = f"/api/community/uploads/community/{user_id}/{secure_name}"
        
        return jsonify({
            'success': True,
            'url': relative_url
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Image upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
        
        result = community_model.get_posts(
            limit=limit,
            offset=offset,
            user_id=user_id
        )
        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
            return jsonify({
                'success': False,
                'error': 'Content is required'
            }), 400
        
        content = data['content'].strip()
        sanskrit_text = data.get('sanskrit_text', '').strip() or None
        analyze_meter = data.get('analyze_meter', True)
        
        # Analyze meter if Sanskrit text is provided
        meter_analysis = None
        if sanskrit_text and analyze_meter:
            try:
                from ..core import Chanda
                from ..config import settings
                
                chanda = Chanda(data_path=str(settings.DATA_DIR))
                analysis_result = chanda.identify_line(sanskrit_text)
                
                if analysis_result.get('found'):
                    meter_analysis = {
                        'meter_name': analysis_result.get('display_chanda_primary', ''),
                        'lg_pattern': ''.join(analysis_result.get('display_lg', [])),
                        'syllable_count': analysis_result.get('display_length', 0),
                        'matra_count': analysis_result.get('display_matra', 0),
                        'gana_pattern': analysis_result.get('display_gana', ''),
                        'found': True
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
            image_url=image_url
        )
        
        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Create post error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
            return jsonify({
                'success': False,
                'error': 'Content is required'
            }), 400
        
        content = data['content'].strip()
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        
        result = community_model.add_comment(post_id, user_id, content)
        
        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Add comment error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
                from ..core import Chanda
                from ..config import settings
                chanda = Chanda(data_path=str(settings.DATA_DIR))
                analysis_result = chanda.identify_line(sanskrit_text)
                if analysis_result and analysis_result.get('found'):
                    meter_analysis = {
                        'found': True,
                        'meter_name': analysis_result.get('display_chanda_primary', ''),
                        'syllables': analysis_result.get('display_length', 0),
                        'pattern': ''.join(analysis_result.get('display_lg', []))
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
            update_image=update_image
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Update post error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
            user_id=user_id,
            bio=data.get('bio'),
            avatar_url=data.get('avatar_url')
        )
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 2: REPORTS & BLOCKS ====================

@community_bp.route('/reports', methods=['POST'])
@require_auth
def report_content(current_user):
    """Report inappropriate content"""
    try:
        data = request.get_json()
        if not data.get('reason'):
            return jsonify({'success': False, 'error': 'Reason is required'}), 400
        
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.report_content(
            reporter_id=user_id,
            reason=data['reason'],
            description=data.get('description'),
            reported_user_id=data.get('user_id'),
            post_id=data.get('post_id'),
            comment_id=data.get('comment_id')
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
            post_id=post_id,
            user_id=user_id,
            content=data['content'].strip(),
            parent_id=comment_id
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


# ==================== PHASE 3: ADMIN MODERATION ====================

@community_bp.route('/admin/reports', methods=['GET'])
@require_auth
def get_all_reports(current_user):
    """
    Get all reports for admin moderation
    Requires admin privileges
    """
    try:
        # Check if user is admin
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        if not community_model.is_admin(user_id):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        status = request.args.get('status', 'pending')  # pending, reviewed, dismissed
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        result = community_model.get_all_reports(status=status, limit=limit, offset=offset)
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        current_app.logger.error(f"Get reports error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/admin/reports/<report_id>/action', methods=['POST'])
@require_auth
def take_report_action(current_user, report_id):
    """
    Take action on a report (dismiss, warn user, delete content, ban user)
    Requires admin privileges
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        if not community_model.is_admin(user_id):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        data = request.get_json()
        action = data.get('action')  # dismiss, delete_content, warn_user, ban_user
        
        if action not in ['dismiss', 'delete_content', 'warn_user', 'ban_user']:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        result = community_model.handle_report(
            report_id=report_id,
            admin_id=user_id,
            action=action,
            notes=data.get('notes')
        )
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        current_app.logger.error(f"Report action error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/admin/stats', methods=['GET'])
@require_auth
def get_moderation_stats(current_user):
    """Get moderation statistics"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        if not community_model.is_admin(user_id):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        result = community_model.get_moderation_stats()
        return jsonify(result), 200 if result.get('success') else 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
