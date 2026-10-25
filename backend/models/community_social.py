"""Follows, feeds, search and user profiles.

Mixed into backend.models.community.CommunityModel.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class SocialMixin:
    # ==================== PHASE 2: FOLLOWS ====================

    def toggle_follow(self, follower_id: str, following_id: str) -> Dict[str, Any]:
        """
        Toggle follow on a user (follow if not following, unfollow if following)
        """
        try:
            if not self.supabase:
                return {'success': True, 'following': True, 'message': 'Follow toggled (local dev)'}

            if follower_id == following_id:
                return {'success': False, 'error': 'Cannot follow yourself'}

            # Check if already following
            existing = (
                self.supabase.table('user_follows')
                .select('id')
                .eq('follower_id', follower_id)
                .eq('following_id', following_id)
                .execute()
            )

            if existing.data:
                # Unfollow
                self.supabase.table('user_follows').delete().eq('follower_id', follower_id).eq(
                    'following_id', following_id
                ).execute()

                # Update counters
                self.supabase.rpc('decrement_followers_count', {'p_user_id': following_id}).execute()
                self.supabase.rpc('decrement_following_count', {'p_user_id': follower_id}).execute()

                return {'success': True, 'following': False, 'message': 'Unfollowed'}
            else:
                # Follow
                self.supabase.table('user_follows').insert(
                    {
                        'follower_id': follower_id,
                        'following_id': following_id,
                        'created_at': datetime.utcnow().isoformat(),
                    }
                ).execute()

                # Update counters
                self.supabase.rpc('increment_followers_count', {'p_user_id': following_id}).execute()
                self.supabase.rpc('increment_following_count', {'p_user_id': follower_id}).execute()

                # Create notification
                self._create_notification(user_id=following_id, type='follow', actor_id=follower_id)

                return {'success': True, 'following': True, 'message': 'Following'}

        except Exception as e:
            print(f"Toggle follow error: {e}")
            return {'success': False, 'error': str(e)}

    def get_followers(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get users who follow a specific user"""
        try:
            if not self.supabase:
                return {'success': True, 'users': [], 'count': 0}

            result = (
                self.supabase.table('user_follows')
                .select('*, users!follower_id(id, username, avatar_url, bio)')
                .eq('following_id', user_id)
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            users = [f.get('users') for f in (result.data or []) if f.get('users')]
            return {'success': True, 'users': users, 'count': len(users)}

        except Exception as e:
            print(f"Get followers error: {e}")
            return {'success': False, 'error': str(e), 'users': []}

    def get_following(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get users that a specific user follows"""
        try:
            if not self.supabase:
                return {'success': True, 'users': [], 'count': 0}

            result = (
                self.supabase.table('user_follows')
                .select('*, users!following_id(id, username, avatar_url, bio)')
                .eq('follower_id', user_id)
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            users = [f.get('users') for f in (result.data or []) if f.get('users')]
            return {'success': True, 'users': users, 'count': len(users)}

        except Exception as e:
            print(f"Get following error: {e}")
            return {'success': False, 'error': str(e), 'users': []}

    def is_following(self, follower_id: str, following_id: str) -> bool:
        """Check if user is following another user"""
        try:
            if not self.supabase:
                return False
            result = (
                self.supabase.table('user_follows')
                .select('id')
                .eq('follower_id', follower_id)
                .eq('following_id', following_id)
                .execute()
            )
            return bool(result.data)
        except Exception:
            return False

    def get_following_feed(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get posts from users that current user follows"""
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}

            # Get list of users being followed
            following = self.supabase.table('user_follows').select('following_id').eq('follower_id', user_id).execute()

            if not following.data:
                return {'success': True, 'posts': [], 'count': 0}

            following_ids = [f['following_id'] for f in following.data]

            # Get posts from followed users
            posts = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .in_('user_id', following_ids)
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return {'success': True, 'posts': posts.data or [], 'count': len(posts.data) if posts.data else 0}

        except Exception as e:
            print(f"Get following feed error: {e}")
            return {'success': False, 'error': str(e), 'posts': []}

    # ==================== PHASE 2: TRENDING ====================

    def get_trending_posts(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get trending posts based on engagement and recency"""
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}

            # Use the trending function
            result = self.supabase.rpc('get_trending_posts', {'p_limit': limit, 'p_offset': offset}).execute()

            if result.data:
                # Fetch user info for each post
                post_ids = [p['id'] for p in result.data]
                posts_with_users = (
                    self.supabase.table('posts')
                    .select('*, users!user_id(id, username, avatar_url)')
                    .in_('id', post_ids)
                    .execute()
                )

                # Maintain trending order
                posts_map = {p['id']: p for p in (posts_with_users.data or [])}
                ordered_posts = [posts_map[pid] for pid in post_ids if pid in posts_map]

                return {'success': True, 'posts': ordered_posts, 'count': len(ordered_posts)}

            return {'success': True, 'posts': [], 'count': 0}

        except Exception as e:
            print(f"Get trending posts error: {e}")
            # Fallback to posts sorted by likes
            return self._get_trending_fallback(limit, offset)

    def _get_trending_fallback(self, limit: int, offset: int) -> Dict[str, Any]:
        """Fallback trending using simple sorting by engagement"""
        try:
            posts = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .gte(
                    'created_at',
                    (
                        datetime.utcnow().replace(hour=0, minute=0, second=0) - __import__('datetime').timedelta(days=7)
                    ).isoformat(),
                )
                .order('likes_count', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return {'success': True, 'posts': posts.data or [], 'count': len(posts.data) if posts.data else 0}
        except Exception as e:
            return {'success': False, 'error': str(e), 'posts': []}

    # ==================== PHASE 2: SEARCH ====================

    def search_posts(self, query: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Search posts by content or Sanskrit text"""
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}

            # Use PostgreSQL full-text search
            search_query = ' | '.join(query.split())  # OR search

            result = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .text_search('search_vector', search_query)
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return {'success': True, 'posts': result.data or [], 'count': len(result.data) if result.data else 0}

        except Exception as e:
            print(f"Search posts error: {e}")
            # Fallback to ILIKE search
            return self._search_posts_fallback(query, limit, offset)

    def _search_posts_fallback(self, query: str, limit: int, offset: int) -> Dict[str, Any]:
        """Fallback search using ILIKE"""
        try:
            result = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .or_(f"content.ilike.%{query}%,sanskrit_text.ilike.%{query}%")
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return {'success': True, 'posts': result.data or [], 'count': len(result.data) if result.data else 0}
        except Exception as e:
            return {'success': False, 'error': str(e), 'posts': []}

    def search_users(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search users by username"""
        try:
            if not self.supabase:
                return {'success': True, 'users': [], 'count': 0}

            result = (
                self.supabase.table('users')
                .select('id, username, avatar_url, bio, followers_count, following_count')
                .ilike('username', f'%{query}%')
                .limit(limit)
                .execute()
            )

            return {'success': True, 'users': result.data or [], 'count': len(result.data) if result.data else 0}

        except Exception as e:
            print(f"Search users error: {e}")
            return {'success': False, 'error': str(e), 'users': []}

    # ==================== PHASE 2: USER PROFILES ====================

    def get_user_profile(self, user_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a user's profile with stats"""
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Supabase not configured'}

            result = (
                self.supabase.table('users')
                .select('id, username, avatar_url, bio, followers_count, following_count, created_at')
                .eq('id', user_id)
                .single()
                .execute()
            )

            if not result.data:
                return {'success': False, 'error': 'User not found'}

            profile = result.data

            # Get post count
            posts_count = self.supabase.table('posts').select('id', count='exact').eq('user_id', user_id).execute()
            profile['posts_count'] = posts_count.count if posts_count.count else 0

            # Check if current user is following
            if current_user_id and current_user_id != user_id:
                profile['is_following'] = self.is_following(current_user_id, user_id)
                profile['is_blocked'] = self._is_blocked(current_user_id, user_id)
            else:
                profile['is_following'] = False
                profile['is_blocked'] = False

            return {'success': True, 'profile': profile}

        except Exception as e:
            print(f"Get user profile error: {e}")
            return {'success': False, 'error': str(e)}

    def update_user_profile(
        self, user_id: str, bio: Optional[str] = None, avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user's profile"""
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Supabase not configured'}

            update_data = {}
            if bio is not None:
                update_data['bio'] = bio
            if avatar_url is not None:
                update_data['avatar_url'] = avatar_url

            if not update_data:
                return {'success': False, 'error': 'No data to update'}

            self.supabase.table('users').update(update_data).eq('id', user_id).execute()

            return {'success': True, 'message': 'Profile updated'}

        except Exception as e:
            return {'success': False, 'error': str(e)}
