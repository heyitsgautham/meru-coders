"""
Community model for handling posts, likes, comments, follows, bookmarks, notifications
Twitter-like social platform for Sanskrit enthusiasts
Phase 2: Full feature set with follows, trending, search, notifications
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from ..config.settings import settings
from supabase import create_client


class CommunityModel:
    """Handle community posts, likes, comments, follows, and more using Supabase"""
    
    def __init__(self):
        # Create client lazily to avoid crashes when env vars are missing during startup
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        else:
            self.supabase = None
    
    # ==================== POSTS ====================
    
    def create_post(self, user_id: str, content: str, sanskrit_text: Optional[str] = None, 
                    meter_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a new post
        
        Args:
            user_id: User ID from auth
            content: Post content/caption
            sanskrit_text: Optional Sanskrit verse text
            meter_analysis: Optional meter analysis result from Chanda
        
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
                        'user_id': user_id,
                        'created_at': datetime.utcnow().isoformat(),
                        'likes_count': 0,
                        'comments_count': 0
                    },
                    'message': 'Post created (local dev fallback)'
                }
            
            post_data = {
                'user_id': user_id,
                'content': content,
                'sanskrit_text': sanskrit_text,
                'meter_analysis': meter_analysis,
                'likes_count': 0,
                'comments_count': 0,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table('posts').insert(post_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'post': result.data[0],
                    'message': 'Post created successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create post'
                }
                
        except Exception as e:
            print(f"Create post error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
                return {
                    'success': True,
                    'posts': [],
                    'count': 0,
                    'message': 'No posts (Supabase not configured)'
                }
            
            query = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            return {
                'success': True,
                'posts': result.data or [],
                'count': len(result.data) if result.data else 0
            }
            
        except Exception as e:
            print(f"Get posts error: {e}")
            return {
                'success': False,
                'error': str(e),
                'posts': []
            }
    
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
                return {
                    'success': False,
                    'error': 'Supabase not configured'
                }
            
            result = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .eq('id', post_id)\
                .single()\
                .execute()
            
            if not result.data:
                return {
                    'success': False,
                    'error': 'Post not found'
                }
            
            post = result.data
            
            # Check if current user has liked this post
            if current_user_id:
                like_check = self.supabase.table('post_likes')\
                    .select('id')\
                    .eq('post_id', post_id)\
                    .eq('user_id', current_user_id)\
                    .execute()
                post['is_liked'] = bool(like_check.data)
            else:
                post['is_liked'] = False
            
            return {
                'success': True,
                'post': post
            }
            
        except Exception as e:
            print(f"Get post error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
                return {
                    'success': True,
                    'message': 'Post deleted (local dev fallback)'
                }
            
            # Verify ownership
            post = self.supabase.table('posts')\
                .select('user_id')\
                .eq('id', post_id)\
                .single()\
                .execute()
            
            if not post.data:
                return {
                    'success': False,
                    'error': 'Post not found'
                }
            
            if post.data['user_id'] != user_id:
                return {
                    'success': False,
                    'error': 'You can only delete your own posts'
                }
            
            # Delete post (cascade will handle likes and comments)
            self.supabase.table('posts').delete().eq('id', post_id).execute()
            
            return {
                'success': True,
                'message': 'Post deleted successfully'
            }
            
        except Exception as e:
            print(f"Delete post error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
                return {
                    'success': True,
                    'liked': True,
                    'message': 'Like toggled (local dev fallback)'
                }
            
            # Check if already liked
            existing = self.supabase.table('post_likes')\
                .select('id')\
                .eq('post_id', post_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if existing.data:
                # Unlike - remove the like
                self.supabase.table('post_likes')\
                    .delete()\
                    .eq('post_id', post_id)\
                    .eq('user_id', user_id)\
                    .execute()
                
                # Decrement likes_count
                self.supabase.rpc('decrement_likes_count', {'p_post_id': post_id}).execute()
                
                return {
                    'success': True,
                    'liked': False,
                    'message': 'Post unliked'
                }
            else:
                # Like - add new like
                self.supabase.table('post_likes').insert({
                    'post_id': post_id,
                    'user_id': user_id,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                
                # Increment likes_count
                self.supabase.rpc('increment_likes_count', {'p_post_id': post_id}).execute()
                
                # Create notification for post owner
                post = self.supabase.table('posts').select('user_id').eq('id', post_id).single().execute()
                if post.data and post.data['user_id'] != user_id:
                    self._create_notification(
                        user_id=post.data['user_id'],
                        type='like',
                        actor_id=user_id,
                        post_id=post_id
                    )
                
                return {
                    'success': True,
                    'liked': True,
                    'message': 'Post liked'
                }
                
        except Exception as e:
            print(f"Toggle like error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
                return {
                    'success': True,
                    'users': [],
                    'count': 0
                }
            
            result = self.supabase.table('post_likes')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .eq('post_id', post_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return {
                'success': True,
                'users': [like.get('users') for like in (result.data or []) if like.get('users')],
                'count': len(result.data) if result.data else 0
            }
            
        except Exception as e:
            print(f"Get post likes error: {e}")
            return {
                'success': False,
                'error': str(e),
                'users': []
            }
    
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
                        'created_at': datetime.utcnow().isoformat()
                    },
                    'message': 'Comment added (local dev fallback)'
                }
            
            comment_data = {
                'post_id': post_id,
                'user_id': user_id,
                'content': content,
                'created_at': datetime.utcnow().isoformat()
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
                        comment_id=result.data[0]['id']
                    )
                
                # Fetch comment with user info
                comment = self.supabase.table('post_comments')\
                    .select('*, users!user_id(id, username, avatar_url)')\
                    .eq('id', result.data[0]['id'])\
                    .single()\
                    .execute()
                
                return {
                    'success': True,
                    'comment': comment.data if comment.data else result.data[0],
                    'message': 'Comment added successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add comment'
                }
                
        except Exception as e:
            print(f"Add comment error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
                return {
                    'success': True,
                    'comments': [],
                    'count': 0
                }
            
            result = self.supabase.table('post_comments')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .eq('post_id', post_id)\
                .order('created_at', desc=False)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return {
                'success': True,
                'comments': result.data or [],
                'count': len(result.data) if result.data else 0
            }
            
        except Exception as e:
            print(f"Get comments error: {e}")
            return {
                'success': False,
                'error': str(e),
                'comments': []
            }
    
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
                return {
                    'success': True,
                    'message': 'Comment deleted (local dev fallback)'
                }
            
            # Verify ownership and get post_id for counter update
            comment = self.supabase.table('post_comments')\
                .select('user_id, post_id')\
                .eq('id', comment_id)\
                .single()\
                .execute()
            
            if not comment.data:
                return {
                    'success': False,
                    'error': 'Comment not found'
                }
            
            if comment.data['user_id'] != user_id:
                return {
                    'success': False,
                    'error': 'You can only delete your own comments'
                }
            
            post_id = comment.data['post_id']
            
            # Delete comment
            self.supabase.table('post_comments').delete().eq('id', comment_id).execute()
            
            # Decrement comments_count
            self.supabase.rpc('decrement_comments_count', {'p_post_id': post_id}).execute()
            
            return {
                'success': True,
                'message': 'Comment deleted successfully'
            }
            
        except Exception as e:
            print(f"Delete comment error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
                return {
                    'success': True,
                    'posts': [],
                    'count': 0
                }
            
            # Get post IDs that user has liked
            likes = self.supabase.table('post_likes')\
                .select('post_id')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            if not likes.data:
                return {
                    'success': True,
                    'posts': [],
                    'count': 0
                }
            
            post_ids = [like['post_id'] for like in likes.data]
            
            # Get full post data
            posts = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .in_('id', post_ids)\
                .execute()
            
            return {
                'success': True,
                'posts': posts.data or [],
                'count': len(posts.data) if posts.data else 0
            }
            
        except Exception as e:
            print(f"Get liked posts error: {e}")
            return {
                'success': False,
                'error': str(e),
                'posts': []
            }

    # ==================== PHASE 2: EDIT POST ====================
    
    def update_post(self, post_id: str, user_id: str, content: Optional[str] = None,
                    sanskrit_text: Optional[str] = None, meter_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Update a post (only by owner)
        
        Args:
            post_id: Post ID to update
            user_id: User ID (must be post owner)
            content: New content (optional)
            sanskrit_text: New Sanskrit text (optional)
            meter_analysis: New meter analysis (optional)
        
        Returns:
            Dict with success status and updated post
        """
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Supabase not configured'}
            
            # Verify ownership
            post = self.supabase.table('posts')\
                .select('user_id')\
                .eq('id', post_id)\
                .single()\
                .execute()
            
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
            
            result = self.supabase.table('posts')\
                .update(update_data)\
                .eq('id', post_id)\
                .execute()
            
            if result.data:
                # Fetch updated post with user info
                updated = self.supabase.table('posts')\
                    .select('*, users!user_id(id, username, avatar_url)')\
                    .eq('id', post_id)\
                    .single()\
                    .execute()
                return {
                    'success': True,
                    'post': updated.data,
                    'message': 'Post updated successfully'
                }
            return {'success': False, 'error': 'Failed to update post'}
            
        except Exception as e:
            print(f"Update post error: {e}")
            return {'success': False, 'error': str(e)}

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
            existing = self.supabase.table('user_follows')\
                .select('id')\
                .eq('follower_id', follower_id)\
                .eq('following_id', following_id)\
                .execute()
            
            if existing.data:
                # Unfollow
                self.supabase.table('user_follows')\
                    .delete()\
                    .eq('follower_id', follower_id)\
                    .eq('following_id', following_id)\
                    .execute()
                
                # Update counters
                self.supabase.rpc('decrement_followers_count', {'p_user_id': following_id}).execute()
                self.supabase.rpc('decrement_following_count', {'p_user_id': follower_id}).execute()
                
                return {'success': True, 'following': False, 'message': 'Unfollowed'}
            else:
                # Follow
                self.supabase.table('user_follows').insert({
                    'follower_id': follower_id,
                    'following_id': following_id,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                
                # Update counters
                self.supabase.rpc('increment_followers_count', {'p_user_id': following_id}).execute()
                self.supabase.rpc('increment_following_count', {'p_user_id': follower_id}).execute()
                
                # Create notification
                self._create_notification(
                    user_id=following_id,
                    type='follow',
                    actor_id=follower_id
                )
                
                return {'success': True, 'following': True, 'message': 'Following'}
                
        except Exception as e:
            print(f"Toggle follow error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_followers(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get users who follow a specific user"""
        try:
            if not self.supabase:
                return {'success': True, 'users': [], 'count': 0}
            
            result = self.supabase.table('user_follows')\
                .select('*, users!follower_id(id, username, avatar_url, bio)')\
                .eq('following_id', user_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
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
            
            result = self.supabase.table('user_follows')\
                .select('*, users!following_id(id, username, avatar_url, bio)')\
                .eq('follower_id', user_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
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
            result = self.supabase.table('user_follows')\
                .select('id')\
                .eq('follower_id', follower_id)\
                .eq('following_id', following_id)\
                .execute()
            return bool(result.data)
        except:
            return False
    
    def get_following_feed(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get posts from users that current user follows"""
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}
            
            # Get list of users being followed
            following = self.supabase.table('user_follows')\
                .select('following_id')\
                .eq('follower_id', user_id)\
                .execute()
            
            if not following.data:
                return {'success': True, 'posts': [], 'count': 0}
            
            following_ids = [f['following_id'] for f in following.data]
            
            # Get posts from followed users
            posts = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .in_('user_id', following_ids)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return {
                'success': True,
                'posts': posts.data or [],
                'count': len(posts.data) if posts.data else 0
            }
            
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
            result = self.supabase.rpc('get_trending_posts', {
                'p_limit': limit,
                'p_offset': offset
            }).execute()
            
            if result.data:
                # Fetch user info for each post
                post_ids = [p['id'] for p in result.data]
                posts_with_users = self.supabase.table('posts')\
                    .select('*, users!user_id(id, username, avatar_url)')\
                    .in_('id', post_ids)\
                    .execute()
                
                # Maintain trending order
                posts_map = {p['id']: p for p in (posts_with_users.data or [])}
                ordered_posts = [posts_map[pid] for pid in post_ids if pid in posts_map]
                
                return {
                    'success': True,
                    'posts': ordered_posts,
                    'count': len(ordered_posts)
                }
            
            return {'success': True, 'posts': [], 'count': 0}
            
        except Exception as e:
            print(f"Get trending posts error: {e}")
            # Fallback to posts sorted by likes
            return self._get_trending_fallback(limit, offset)
    
    def _get_trending_fallback(self, limit: int, offset: int) -> Dict[str, Any]:
        """Fallback trending using simple sorting by engagement"""
        try:
            posts = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .gte('created_at', (datetime.utcnow().replace(hour=0, minute=0, second=0) - 
                     __import__('datetime').timedelta(days=7)).isoformat())\
                .order('likes_count', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return {
                'success': True,
                'posts': posts.data or [],
                'count': len(posts.data) if posts.data else 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'posts': []}

    # ==================== PHASE 2: BOOKMARKS ====================
    
    def toggle_bookmark(self, post_id: str, user_id: str) -> Dict[str, Any]:
        """Toggle bookmark on a post"""
        try:
            if not self.supabase:
                return {'success': True, 'bookmarked': True}
            
            existing = self.supabase.table('bookmarks')\
                .select('id')\
                .eq('post_id', post_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if existing.data:
                # Remove bookmark
                self.supabase.table('bookmarks')\
                    .delete()\
                    .eq('post_id', post_id)\
                    .eq('user_id', user_id)\
                    .execute()
                return {'success': True, 'bookmarked': False, 'message': 'Bookmark removed'}
            else:
                # Add bookmark
                self.supabase.table('bookmarks').insert({
                    'post_id': post_id,
                    'user_id': user_id,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                return {'success': True, 'bookmarked': True, 'message': 'Post bookmarked'}
                
        except Exception as e:
            print(f"Toggle bookmark error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_bookmarked_posts(self, user_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get posts bookmarked by user"""
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}
            
            bookmarks = self.supabase.table('bookmarks')\
                .select('post_id')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            if not bookmarks.data:
                return {'success': True, 'posts': [], 'count': 0}
            
            post_ids = [b['post_id'] for b in bookmarks.data]
            
            posts = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .in_('id', post_ids)\
                .execute()
            
            # Maintain bookmark order
            posts_map = {p['id']: p for p in (posts.data or [])}
            ordered_posts = [posts_map[pid] for pid in post_ids if pid in posts_map]
            
            return {
                'success': True,
                'posts': ordered_posts,
                'count': len(ordered_posts)
            }
            
        except Exception as e:
            print(f"Get bookmarked posts error: {e}")
            return {'success': False, 'error': str(e), 'posts': []}
    
    def is_bookmarked(self, post_id: str, user_id: str) -> bool:
        """Check if post is bookmarked by user"""
        try:
            if not self.supabase:
                return False
            result = self.supabase.table('bookmarks')\
                .select('id')\
                .eq('post_id', post_id)\
                .eq('user_id', user_id)\
                .execute()
            return bool(result.data)
        except:
            return False

    # ==================== PHASE 2: SEARCH ====================
    
    def search_posts(self, query: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Search posts by content or Sanskrit text"""
        try:
            if not self.supabase:
                return {'success': True, 'posts': [], 'count': 0}
            
            # Use PostgreSQL full-text search
            search_query = ' | '.join(query.split())  # OR search
            
            result = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .text_search('search_vector', search_query)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return {
                'success': True,
                'posts': result.data or [],
                'count': len(result.data) if result.data else 0
            }
            
        except Exception as e:
            print(f"Search posts error: {e}")
            # Fallback to ILIKE search
            return self._search_posts_fallback(query, limit, offset)
    
    def _search_posts_fallback(self, query: str, limit: int, offset: int) -> Dict[str, Any]:
        """Fallback search using ILIKE"""
        try:
            result = self.supabase.table('posts')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .or_(f"content.ilike.%{query}%,sanskrit_text.ilike.%{query}%")\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return {
                'success': True,
                'posts': result.data or [],
                'count': len(result.data) if result.data else 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'posts': []}
    
    def search_users(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search users by username"""
        try:
            if not self.supabase:
                return {'success': True, 'users': [], 'count': 0}
            
            result = self.supabase.table('users')\
                .select('id, username, avatar_url, bio, followers_count, following_count')\
                .ilike('username', f'%{query}%')\
                .limit(limit)\
                .execute()
            
            return {
                'success': True,
                'users': result.data or [],
                'count': len(result.data) if result.data else 0
            }
            
        except Exception as e:
            print(f"Search users error: {e}")
            return {'success': False, 'error': str(e), 'users': []}

    # ==================== PHASE 2: NOTIFICATIONS ====================
    
    def _create_notification(self, user_id: str, type: str, actor_id: str,
                            post_id: Optional[str] = None, comment_id: Optional[str] = None,
                            content: Optional[str] = None) -> None:
        """Create a notification (internal helper)"""
        try:
            if not self.supabase or user_id == actor_id:
                return  # Don't notify yourself
            
            self.supabase.table('notifications').insert({
                'user_id': user_id,
                'type': type,
                'actor_id': actor_id,
                'post_id': post_id,
                'comment_id': comment_id,
                'content': content,
                'is_read': False,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"Create notification error: {e}")
    
    def get_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> Dict[str, Any]:
        """Get notifications for a user"""
        try:
            if not self.supabase:
                return {'success': True, 'notifications': [], 'unread_count': 0}
            
            query = self.supabase.table('notifications')\
                .select('*, actor:users!actor_id(id, username, avatar_url), post:posts!post_id(id, content)')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)
            
            if unread_only:
                query = query.eq('is_read', False)
            
            result = query.execute()
            
            # Get unread count
            unread = self.supabase.table('notifications')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .eq('is_read', False)\
                .execute()
            
            return {
                'success': True,
                'notifications': result.data or [],
                'unread_count': unread.count if unread.count else 0
            }
            
        except Exception as e:
            print(f"Get notifications error: {e}")
            return {'success': False, 'error': str(e), 'notifications': [], 'unread_count': 0}
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Mark a notification as read"""
        try:
            if not self.supabase:
                return {'success': True}
            
            self.supabase.table('notifications')\
                .update({'is_read': True})\
                .eq('id', notification_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return {'success': True, 'message': 'Notification marked as read'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def mark_all_notifications_read(self, user_id: str) -> Dict[str, Any]:
        """Mark all notifications as read for a user"""
        try:
            if not self.supabase:
                return {'success': True}
            
            self.supabase.table('notifications')\
                .update({'is_read': True})\
                .eq('user_id', user_id)\
                .eq('is_read', False)\
                .execute()
            
            return {'success': True, 'message': 'All notifications marked as read'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ==================== PHASE 2: USER PROFILES ====================
    
    def get_user_profile(self, user_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a user's profile with stats"""
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Supabase not configured'}
            
            result = self.supabase.table('users')\
                .select('id, username, avatar_url, bio, followers_count, following_count, created_at')\
                .eq('id', user_id)\
                .single()\
                .execute()
            
            if not result.data:
                return {'success': False, 'error': 'User not found'}
            
            profile = result.data
            
            # Get post count
            posts_count = self.supabase.table('posts')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
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
    
    def update_user_profile(self, user_id: str, bio: Optional[str] = None,
                           avatar_url: Optional[str] = None) -> Dict[str, Any]:
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
            
            result = self.supabase.table('users')\
                .update(update_data)\
                .eq('id', user_id)\
                .execute()
            
            return {'success': True, 'message': 'Profile updated'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ==================== PHASE 2: REPORTS & BLOCKS ====================
    
    def report_content(self, reporter_id: str, reason: str, description: Optional[str] = None,
                      reported_user_id: Optional[str] = None, post_id: Optional[str] = None,
                      comment_id: Optional[str] = None) -> Dict[str, Any]:
        """Report inappropriate content"""
        try:
            if not self.supabase:
                return {'success': True, 'message': 'Report submitted'}
            
            if not any([reported_user_id, post_id, comment_id]):
                return {'success': False, 'error': 'Must specify content to report'}
            
            self.supabase.table('reports').insert({
                'reporter_id': reporter_id,
                'reported_user_id': reported_user_id,
                'post_id': post_id,
                'comment_id': comment_id,
                'reason': reason,
                'description': description,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return {'success': True, 'message': 'Report submitted successfully'}
            
        except Exception as e:
            print(f"Report content error: {e}")
            return {'success': False, 'error': str(e)}
    
    def toggle_block(self, blocker_id: str, blocked_id: str) -> Dict[str, Any]:
        """Toggle block on a user"""
        try:
            if not self.supabase:
                return {'success': True, 'blocked': True}
            
            if blocker_id == blocked_id:
                return {'success': False, 'error': 'Cannot block yourself'}
            
            existing = self.supabase.table('user_blocks')\
                .select('id')\
                .eq('blocker_id', blocker_id)\
                .eq('blocked_id', blocked_id)\
                .execute()
            
            if existing.data:
                # Unblock
                self.supabase.table('user_blocks')\
                    .delete()\
                    .eq('blocker_id', blocker_id)\
                    .eq('blocked_id', blocked_id)\
                    .execute()
                return {'success': True, 'blocked': False, 'message': 'User unblocked'}
            else:
                # Block - also unfollow if following
                self.supabase.table('user_blocks').insert({
                    'blocker_id': blocker_id,
                    'blocked_id': blocked_id,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                
                # Remove any existing follow relationship
                self.supabase.table('user_follows')\
                    .delete()\
                    .eq('follower_id', blocker_id)\
                    .eq('following_id', blocked_id)\
                    .execute()
                self.supabase.table('user_follows')\
                    .delete()\
                    .eq('follower_id', blocked_id)\
                    .eq('following_id', blocker_id)\
                    .execute()
                
                return {'success': True, 'blocked': True, 'message': 'User blocked'}
                
        except Exception as e:
            print(f"Toggle block error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _is_blocked(self, user_id: str, other_user_id: str) -> bool:
        """Check if users have blocked each other"""
        try:
            if not self.supabase:
                return False
            result = self.supabase.table('user_blocks')\
                .select('id')\
                .or_(f"blocker_id.eq.{user_id},blocker_id.eq.{other_user_id}")\
                .or_(f"blocked_id.eq.{user_id},blocked_id.eq.{other_user_id}")\
                .execute()
            return bool(result.data)
        except:
            return False
    
    def get_blocked_users(self, user_id: str) -> Dict[str, Any]:
        """Get list of users blocked by current user"""
        try:
            if not self.supabase:
                return {'success': True, 'users': []}
            
            result = self.supabase.table('user_blocks')\
                .select('*, users!blocked_id(id, username, avatar_url)')\
                .eq('blocker_id', user_id)\
                .execute()
            
            users = [b.get('users') for b in (result.data or []) if b.get('users')]
            return {'success': True, 'users': users}
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'users': []}

    # ==================== PHASE 2: COMMENT REPLIES ====================
    
    def add_comment_reply(self, post_id: str, user_id: str, content: str, 
                         parent_id: str) -> Dict[str, Any]:
        """Add a reply to a comment"""
        try:
            if not self.supabase:
                return {'success': True, 'comment': {'id': 'local', 'content': content}}
            
            # Verify parent comment exists
            parent = self.supabase.table('post_comments')\
                .select('id, user_id, post_id')\
                .eq('id', parent_id)\
                .single()\
                .execute()
            
            if not parent.data:
                return {'success': False, 'error': 'Parent comment not found'}
            
            comment_data = {
                'post_id': post_id,
                'user_id': user_id,
                'content': content,
                'parent_id': parent_id,
                'created_at': datetime.utcnow().isoformat()
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
                        comment_id=result.data[0]['id']
                    )
                
                # Fetch with user info
                comment = self.supabase.table('post_comments')\
                    .select('*, users!user_id(id, username, avatar_url)')\
                    .eq('id', result.data[0]['id'])\
                    .single()\
                    .execute()
                
                return {
                    'success': True,
                    'comment': comment.data if comment.data else result.data[0]
                }
            
            return {'success': False, 'error': 'Failed to add reply'}
            
        except Exception as e:
            print(f"Add comment reply error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_comment_replies(self, comment_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get replies to a comment"""
        try:
            if not self.supabase:
                return {'success': True, 'replies': []}
            
            result = self.supabase.table('post_comments')\
                .select('*, users!user_id(id, username, avatar_url)')\
                .eq('parent_id', comment_id)\
                .order('created_at', desc=False)\
                .limit(limit)\
                .execute()
            
            return {
                'success': True,
                'replies': result.data or [],
                'count': len(result.data) if result.data else 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'replies': []}
