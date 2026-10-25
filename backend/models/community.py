"""
Community model for handling posts, likes, comments, follows, bookmarks, notifications
Twitter-like social platform for Sanskrit enthusiasts
Phase 2: Full feature set with follows, trending, search, notifications
"""

from supabase import create_client

from backend.models.community_engagement import EngagementMixin
from backend.models.community_moderation import ModerationMixin
from backend.models.community_posts import PostsMixin
from backend.models.community_social import SocialMixin

from ..config.settings import settings


class CommunityModel(PostsMixin, EngagementMixin, SocialMixin, ModerationMixin):
    """Handle community posts, likes, comments, follows, and more using Supabase"""

    def __init__(self):
        # Create client lazily to avoid crashes when env vars are missing during startup
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        else:
            self.supabase = None
