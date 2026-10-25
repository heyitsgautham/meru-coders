"""
Community API Routes
Twitter-like social platform for Sanskrit enthusiasts
Handles posts, likes, comments, and image uploads
"""

from flask import Blueprint

from ...models.community import CommunityModel

community_bp = Blueprint('community', __name__)
community_model = CommunityModel()

# Image upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Each submodule registers its routes on community_bp when imported.
from . import comments, moderation, posts, social, uploads  # noqa: E402, F401
