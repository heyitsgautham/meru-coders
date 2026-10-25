"""Creating, reading, editing and deleting community posts.

Mixed into backend.models.community.CommunityModel.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class PostsMixin:
    # ==================== POSTS ====================

    def create_post(
        self,
        user_id: str,
        content: str,
        sanskrit_text: Optional[str] = None,
        meter_analysis: Optional[Dict] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new post

        Args:
            user_id: User ID from auth
            content: Post content/caption
            sanskrit_text: Optional Sanskrit verse text
            meter_analysis: Optional meter analysis result from Chanda
            image_url: Optional URL of uploaded image

        Returns:
            Dict with success status and post data
        """
        try:
            if not self.supabase:
                return {
                    'success': True,
                    'post': {
                        'id': f"local-{user_id}-{datetime.utcnow().timestamp()}",
                        'content': content,
                        'sanskrit_text': sanskrit_text,
                        'meter_analysis': meter_analysis,
                        'image_url': image_url,
                        'user_id': user_id,
                        'created_at': datetime.utcnow().isoformat(),
                        'likes_count': 0,
                        'comments_count': 0,
                    },
                    'message': 'Post created (local dev fallback)',
                }

            post_data = {
                'user_id': user_id,
                'content': content,
                'sanskrit_text': sanskrit_text,
                'meter_analysis': meter_analysis,
                'image_url': image_url,
                'likes_count': 0,
                'comments_count': 0,
                'created_at': datetime.utcnow().isoformat(),
            }

            result = self.supabase.table('posts').insert(post_data).execute()

            if result.data:
                return {'success': True, 'post': result.data[0], 'message': 'Post created successfully'}
            else:
                return {'success': False, 'error': 'Failed to create post'}

        except Exception as e:
            print(f"Create post error: {e}")
            return {'success': False, 'error': str(e)}

    def get_posts(self, limit: int = 20, offset: int = 0, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get posts with pagination (chronological order)

        Args:
            limit: Number of posts to return
            offset: Pagination offset
            user_id: Optional - filter by user ID

        Returns:
            Dict with posts list
        """
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0, 'message': 'No posts (Supabase not configured)'}

            query = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
            )

            if user_id:
                query = query.eq('user_id', user_id)

            result = query.execute()

            return {'success': True, 'posts': result.data or [], 'count': len(result.data) if result.data else 0}

        except Exception as e:
            print(f"Get posts error: {e}")
            return {'success': False, 'error': str(e), 'posts': []}

    def get_post_by_id(self, post_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a single post by ID with like status for current user

        Args:
            post_id: Post ID
            current_user_id: Optional - current user ID to check if liked

        Returns:
            Dict with post data
        """
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Supabase not configured'}

            result = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .eq('id', post_id)
                .single()
                .execute()
            )

            if not result.data:
                return {'success': False, 'error': 'Post not found'}

            post = result.data

            # Check if current user has liked this post
            if current_user_id:
                like_check = (
                    self.supabase.table('post_likes')
                    .select('id')
                    .eq('post_id', post_id)
                    .eq('user_id', current_user_id)
                    .execute()
                )
                post['is_liked'] = bool(like_check.data)
            else:
                post['is_liked'] = False

            return {'success': True, 'post': post}

        except Exception as e:
            print(f"Get post error: {e}")
            return {'success': False, 'error': str(e)}

    def delete_post(self, post_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete a post (only by owner)

        Args:
            post_id: Post ID to delete
            user_id: User ID (must be post owner)

        Returns:
            Dict with success status
        """
        try:
            if not self.supabase:
                return {'success': True, 'message': 'Post deleted (local dev fallback)'}

            # Verify ownership
            post = self.supabase.table('posts').select('user_id').eq('id', post_id).single().execute()

            if not post.data:
                return {'success': False, 'error': 'Post not found'}

            if post.data['user_id'] != user_id:
                return {'success': False, 'error': 'You can only delete your own posts'}

            # Delete related records first to handle foreign key constraints
            # Delete bookmarks for this post
            try:
                self.supabase.table('bookmarks').delete().eq('post_id', post_id).execute()
            except Exception as e:
                print(f"Warning: Could not delete bookmarks: {e}")

            # Delete likes for this post
            try:
                self.supabase.table('post_likes').delete().eq('post_id', post_id).execute()
            except Exception as e:
                print(f"Warning: Could not delete likes: {e}")

            # Delete comments for this post
            try:
                self.supabase.table('comments').delete().eq('post_id', post_id).execute()
            except Exception as e:
                print(f"Warning: Could not delete comments: {e}")

            # Delete notifications related to this post
            try:
                self.supabase.table('notifications').delete().eq('post_id', post_id).execute()
            except Exception as e:
                print(f"Warning: Could not delete notifications: {e}")

            # Delete reports for this post
            try:
                self.supabase.table('reports').delete().eq('post_id', post_id).execute()
            except Exception as e:
                print(f"Warning: Could not delete reports: {e}")

            # Now delete the post
            self.supabase.table('posts').delete().eq('id', post_id).execute()

            return {'success': True, 'message': 'Post deleted successfully'}

        except Exception as e:
            print(f"Delete post error: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== USER FEED ====================

    def get_user_posts(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Get posts by a specific user

        Args:
            user_id: User ID to get posts for
            limit: Number of posts to return
            offset: Pagination offset

        Returns:
            Dict with posts list
        """
        return self.get_posts(limit=limit, offset=offset, user_id=user_id)

    def get_liked_posts(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Get posts liked by a user

        Args:
            user_id: User ID
            limit: Number of posts to return
            offset: Pagination offset

        Returns:
            Dict with posts list
        """
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}

            # Get post IDs that user has liked
            likes = (
                self.supabase.table('post_likes')
                .select('post_id')
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            if not likes.data:
                return {'success': True, 'posts': [], 'count': 0}

            post_ids = [like['post_id'] for like in likes.data]

            # Get full post data
            posts = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .in_('id', post_ids)
                .execute()
            )

            return {'success': True, 'posts': posts.data or [], 'count': len(posts.data) if posts.data else 0}

        except Exception as e:
            print(f"Get liked posts error: {e}")
            return {'success': False, 'error': str(e), 'posts': []}

    # ==================== PHASE 2: EDIT POST ====================

    def update_post(
        self,
        post_id: str,
        user_id: str,
        content: Optional[str] = None,
        sanskrit_text: Optional[str] = None,
        meter_analysis: Optional[Dict] = None,
        image_url: Optional[str] = None,
        update_image: bool = False,
    ) -> Dict[str, Any]:
        """
        Update a post (only by owner)

        Args:
            post_id: Post ID to update
            user_id: User ID (must be post owner)
            content: New content (optional)
            sanskrit_text: New Sanskrit text (optional)
            meter_analysis: New meter analysis (optional)
            image_url: Image URL (optional)
            update_image: If True, update image_url field (allows setting to None to remove)

        Returns:
            Dict with success status and updated post
        """
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Supabase not configured'}

            # Verify ownership
            post = self.supabase.table('posts').select('user_id').eq('id', post_id).single().execute()

            if not post.data:
                return {'success': False, 'error': 'Post not found'}

            if post.data['user_id'] != user_id:
                return {'success': False, 'error': 'You can only edit your own posts'}

            # Build update data
            update_data = {'updated_at': datetime.utcnow().isoformat()}
            if content is not None:
                update_data['content'] = content
            if sanskrit_text is not None:
                update_data['sanskrit_text'] = sanskrit_text
            if meter_analysis is not None:
                update_data['meter_analysis'] = meter_analysis
            if update_image:
                # Explicitly update image_url (can be None to remove)
                update_data['image_url'] = image_url

            result = self.supabase.table('posts').update(update_data).eq('id', post_id).execute()

            if result.data:
                # Fetch updated post with user info
                updated = (
                    self.supabase.table('posts')
                    .select('*, users!user_id(id, username, avatar_url)')
                    .eq('id', post_id)
                    .single()
                    .execute()
                )
                return {'success': True, 'post': updated.data, 'message': 'Post updated successfully'}
            return {'success': False, 'error': 'Failed to update post'}

        except Exception as e:
            print(f"Update post error: {e}")
            return {'success': False, 'error': str(e)}
