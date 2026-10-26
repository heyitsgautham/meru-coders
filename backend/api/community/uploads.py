"""Community image uploads: storing post images and serving them back."""

import uuid
from datetime import datetime

from flask import current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from ...auth.middleware import require_auth
from ...config.settings import settings
from . import ALLOWED_EXTENSIONS, MAX_IMAGE_SIZE, allowed_file, community_bp, community_model

# ==================== SERVE UPLOADED FILES ====================


@community_bp.route('/uploads/<path:filepath>', methods=['GET'])
def serve_upload(filepath):
    """
    Serve uploaded files (images, etc.)
    This handles URLs like /api/community/uploads/community/{user_id}/{filename}
    """
    try:
        # The filepath will be like: community/{user_id}/{filename}
        # Only community post images; OCR, document and audio uploads share UPLOADS_DIR.
        if not filepath.startswith('community/'):
            return jsonify({'error': 'File not found'}), 404
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
            return jsonify(
                {'success': False, 'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}
            ), 400

        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        if size > MAX_IMAGE_SIZE:
            return jsonify({'success': False, 'error': 'Image too large. Maximum size is 5MB'}), 400

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

                community_model.supabase.storage.from_('community-images').upload(
                    file_path, file_content, {'content-type': file.content_type}
                )

                # Get public URL
                public_url = community_model.supabase.storage.from_('community-images').get_public_url(file_path)

                return jsonify({'success': True, 'url': public_url}), 200

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

        return jsonify({'success': True, 'url': relative_url}), 200

    except Exception as e:
        current_app.logger.error(f"Image upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
