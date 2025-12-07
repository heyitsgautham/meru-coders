"""
Community model for handling posts, likes, and comments
Twitter-like social platform for Sanskrit enthusiasts
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from ..config.settings import settings
from supabase import create_client


class CommunityModel:
    """Handle community posts, likes, and comments using Supabase"""
    
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
