"""Likes, comments, replies and bookmarks on community posts.

Mixed into backend.models.community.CommunityModel.
"""

from datetime import datetime
from typing import Any, Dict


class EngagementMixin:
    # ==================== LIKES ====================

    def toggle_like(self, post_id: str, user_id: str) -> Dict[str, Any]:
        """
        Toggle like on a post (like if not liked, unlike if liked)

        Args:
            post_id: Post ID
            user_id: User ID

        Returns:
            Dict with success status and new like state
        """
        try:
            if not self.supabase:
                return {'success': True, 'liked': True, 'message': 'Like toggled (local dev fallback)'}

            # Check if already liked
            existing = (
                self.supabase.table('post_likes').select('id').eq('post_id', post_id).eq('user_id', user_id).execute()
            )

            if existing.data:
                # Unlike - remove the like
                self.supabase.table('post_likes').delete().eq('post_id', post_id).eq('user_id', user_id).execute()

                # Decrement likes_count
                self.supabase.rpc('decrement_likes_count', {'p_post_id': post_id}).execute()

                return {'success': True, 'liked': False, 'message': 'Post unliked'}
            else:
                # Like - add new like
                self.supabase.table('post_likes').insert(
                    {'post_id': post_id, 'user_id': user_id, 'created_at': datetime.utcnow().isoformat()}
                ).execute()

                # Increment likes_count
                self.supabase.rpc('increment_likes_count', {'p_post_id': post_id}).execute()

                # Create notification for post owner
                post = self.supabase.table('posts').select('user_id').eq('id', post_id).single().execute()
                if post.data and post.data['user_id'] != user_id:
                    self._create_notification(
                        user_id=post.data['user_id'], type='like', actor_id=user_id, post_id=post_id
                    )

                return {'success': True, 'liked': True, 'message': 'Post liked'}

        except Exception as e:
            print(f"Toggle like error: {e}")
            return {'success': False, 'error': str(e)}

    def get_post_likes(self, post_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get users who liked a post

        Args:
            post_id: Post ID
            limit: Max users to return

        Returns:
            Dict with users who liked the post
        """
        try:
            if not self.supabase:
                return {'success': True, 'users': [], 'count': 0}

            result = (
                self.supabase.table('post_likes')
                .select('*, users!user_id(id, username, avatar_url)')
                .eq('post_id', post_id)
                .order('created_at', desc=True)
                .limit(limit)
                .execute()
            )

            return {
                'success': True,
                'users': [like.get('users') for like in (result.data or []) if like.get('users')],
                'count': len(result.data) if result.data else 0,
            }

        except Exception as e:
            print(f"Get post likes error: {e}")
            return {'success': False, 'error': str(e), 'users': []}

    # ==================== COMMENTS ====================

    def add_comment(self, post_id: str, user_id: str, content: str) -> Dict[str, Any]:
        """
        Add a comment to a post

        Args:
            post_id: Post ID
            user_id: User ID
            content: Comment content

        Returns:
            Dict with success status and comment data
        """
        try:
            if not self.supabase:
                return {
                    'success': True,
                    'comment': {
                        'id': f"local-comment-{datetime.utcnow().timestamp()}",
                        'content': content,
                        'user_id': user_id,
                        'post_id': post_id,
                        'created_at': datetime.utcnow().isoformat(),
                    },
                    'message': 'Comment added (local dev fallback)',
                }

            comment_data = {
                'post_id': post_id,
                'user_id': user_id,
                'content': content,
                'created_at': datetime.utcnow().isoformat(),
            }

            result = self.supabase.table('post_comments').insert(comment_data).execute()

            if result.data:
                # Increment comments_count
                self.supabase.rpc('increment_comments_count', {'p_post_id': post_id}).execute()

                # Create notification for post owner
                post = self.supabase.table('posts').select('user_id').eq('id', post_id).single().execute()
                if post.data and post.data['user_id'] != user_id:
                    self._create_notification(
                        user_id=post.data['user_id'],
                        type='comment',
                        actor_id=user_id,
                        post_id=post_id,
                        comment_id=result.data[0]['id'],
                    )

                # Fetch comment with user info
                comment = (
                    self.supabase.table('post_comments')
                    .select('*, users!user_id(id, username, avatar_url)')
                    .eq('id', result.data[0]['id'])
                    .single()
                    .execute()
                )

                return {
                    'success': True,
                    'comment': comment.data if comment.data else result.data[0],
                    'message': 'Comment added successfully',
                }
            else:
                return {'success': False, 'error': 'Failed to add comment'}

        except Exception as e:
            print(f"Add comment error: {e}")
            return {'success': False, 'error': str(e)}

    def get_comments(self, post_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get comments for a post

        Args:
            post_id: Post ID
            limit: Number of comments to return
            offset: Pagination offset

        Returns:
            Dict with comments list
        """
        try:
            if not self.supabase:
                return {'success': True, 'comments': [], 'count': 0}

            result = (
                self.supabase.table('post_comments')
                .select('*, users!user_id(id, username, avatar_url)')
                .eq('post_id', post_id)
                .order('created_at', desc=False)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return {'success': True, 'comments': result.data or [], 'count': len(result.data) if result.data else 0}

        except Exception as e:
            print(f"Get comments error: {e}")
            return {'success': False, 'error': str(e), 'comments': []}

    def delete_comment(self, comment_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete a comment (only by owner)

        Args:
            comment_id: Comment ID to delete
            user_id: User ID (must be comment owner)

        Returns:
            Dict with success status
        """
        try:
            if not self.supabase:
                return {'success': True, 'message': 'Comment deleted (local dev fallback)'}

            # Verify ownership and get post_id for counter update
            comment = (
                self.supabase.table('post_comments').select('user_id, post_id').eq('id', comment_id).single().execute()
            )

            if not comment.data:
                return {'success': False, 'error': 'Comment not found'}

            if comment.data['user_id'] != user_id:
                return {'success': False, 'error': 'You can only delete your own comments'}

            post_id = comment.data['post_id']

            # Delete comment
            self.supabase.table('post_comments').delete().eq('id', comment_id).execute()

            # Decrement comments_count
            self.supabase.rpc('decrement_comments_count', {'p_post_id': post_id}).execute()

            return {'success': True, 'message': 'Comment deleted successfully'}

        except Exception as e:
            print(f"Delete comment error: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== PHASE 2: BOOKMARKS ====================

    def toggle_bookmark(self, post_id: str, user_id: str) -> Dict[str, Any]:
        """Toggle bookmark on a post"""
        try:
            if not self.supabase:
                return {'success': True, 'bookmarked': True}

            existing = (
                self.supabase.table('bookmarks').select('id').eq('post_id', post_id).eq('user_id', user_id).execute()
            )

            if existing.data:
                # Remove bookmark
                self.supabase.table('bookmarks').delete().eq('post_id', post_id).eq('user_id', user_id).execute()
                return {'success': True, 'bookmarked': False, 'message': 'Bookmark removed'}
            else:
                # Add bookmark
                self.supabase.table('bookmarks').insert(
                    {'post_id': post_id, 'user_id': user_id, 'created_at': datetime.utcnow().isoformat()}
                ).execute()
                return {'success': True, 'bookmarked': True, 'message': 'Post bookmarked'}

        except Exception as e:
            print(f"Toggle bookmark error: {e}")
            return {'success': False, 'error': str(e)}

    def get_bookmarked_posts(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get posts bookmarked by user"""
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}

            bookmarks = (
                self.supabase.table('bookmarks')
                .select('post_id')
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            if not bookmarks.data:
                return {'success': True, 'posts': [], 'count': 0}

            post_ids = [b['post_id'] for b in bookmarks.data]

            posts = (
                self.supabase.table('posts')
                .select('*, users!user_id(id, username, avatar_url)')
                .in_('id', post_ids)
                .execute()
            )

            # Maintain bookmark order
            posts_map = {p['id']: p for p in (posts.data or [])}
            ordered_posts = [posts_map[pid] for pid in post_ids if pid in posts_map]

            # All posts in bookmarks are bookmarked by definition
            for post in ordered_posts:
                post['is_bookmarked'] = True

            return {'success': True, 'posts': ordered_posts, 'count': len(ordered_posts)}

        except Exception as e:
            print(f"Get bookmarked posts error: {e}")
            return {'success': False, 'error': str(e), 'posts': []}

    def is_bookmarked(self, post_id: str, user_id: str) -> bool:
        """Check if post is bookmarked by user"""
        try:
            if not self.supabase:
                return False
            result = (
                self.supabase.table('bookmarks').select('id').eq('post_id', post_id).eq('user_id', user_id).execute()
            )
            return bool(result.data)
        except Exception:
            return False

    # ==================== PHASE 2: COMMENT REPLIES ====================

    def add_comment_reply(self, post_id: str, user_id: str, content: str, parent_id: str) -> Dict[str, Any]:
        """Add a reply to a comment"""
        try:
            if not self.supabase:
                return {'success': True, 'comment': {'id': 'local', 'content': content}}

            # Verify parent comment exists
            parent = (
                self.supabase.table('post_comments')
                .select('id, user_id, post_id')
                .eq('id', parent_id)
                .single()
                .execute()
            )

            if not parent.data:
                return {'success': False, 'error': 'Parent comment not found'}

            comment_data = {
                'post_id': post_id,
                'user_id': user_id,
                'content': content,
                'parent_id': parent_id,
                'created_at': datetime.utcnow().isoformat(),
            }

            result = self.supabase.table('post_comments').insert(comment_data).execute()

            if result.data:
                # Increment comments_count
                self.supabase.rpc('increment_comments_count', {'p_post_id': post_id}).execute()

                # Create notification for parent comment author
                if parent.data['user_id'] != user_id:
                    self._create_notification(
                        user_id=parent.data['user_id'],
                        type='reply',
                        actor_id=user_id,
                        post_id=post_id,
                        comment_id=result.data[0]['id'],
                    )

                # Fetch with user info
                comment = (
                    self.supabase.table('post_comments')
                    .select('*, users!user_id(id, username, avatar_url)')
                    .eq('id', result.data[0]['id'])
                    .single()
                    .execute()
                )

                return {'success': True, 'comment': comment.data if comment.data else result.data[0]}

            return {'success': False, 'error': 'Failed to add reply'}

        except Exception as e:
            print(f"Add comment reply error: {e}")
            return {'success': False, 'error': str(e)}

    def get_comment_replies(self, comment_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get replies to a comment"""
        try:
            if not self.supabase:
                return {'success': True, 'replies': []}

            result = (
                self.supabase.table('post_comments')
                .select('*, users!user_id(id, username, avatar_url)')
                .eq('parent_id', comment_id)
                .order('created_at', desc=False)
                .limit(limit)
                .execute()
            )

            return {'success': True, 'replies': result.data or [], 'count': len(result.data) if result.data else 0}

        except Exception as e:
            return {'success': False, 'error': str(e), 'replies': []}
