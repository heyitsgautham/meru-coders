"""Notifications, reports, blocking and admin moderation.

Mixed into backend.models.community.CommunityModel.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class ModerationMixin:
    # ==================== PHASE 2: NOTIFICATIONS ====================

    def _create_notification(
        self,
        user_id: str,
        type: str,
        actor_id: str,
        post_id: Optional[str] = None,
        comment_id: Optional[str] = None,
        content: Optional[str] = None,
    ) -> None:
        """Create a notification (internal helper) and send real-time update"""
        try:
            if not self.supabase or user_id == actor_id:
                return  # Don't notify yourself

            notification_data = {
                'user_id': user_id,
                'type': type,
                'actor_id': actor_id,
                'post_id': post_id,
                'comment_id': comment_id,
                'content': content,
                'is_read': False,
                'created_at': datetime.utcnow().isoformat(),
            }

            result = self.supabase.table('notifications').insert(notification_data).execute()

            # Send real-time notification via WebSocket
            if result.data and len(result.data) > 0:
                notification = result.data[0]

                # Get actor info for the notification
                try:
                    actor = (
                        self.supabase.table('users')
                        .select('id, username, avatar_url')
                        .eq('id', actor_id)
                        .single()
                        .execute()
                    )

                    if actor.data:
                        notification['actor'] = actor.data
                except Exception:
                    pass

                # Send via WebSocket
                try:
                    from backend.api.websocket import emit_notification_count, send_notification_to_user

                    send_notification_to_user(user_id, notification)

                    # Also send updated unread count
                    unread = (
                        self.supabase.table('notifications')
                        .select('id', count='exact')
                        .eq('user_id', user_id)
                        .eq('is_read', False)
                        .execute()
                    )

                    if unread.count:
                        emit_notification_count(user_id, unread.count)
                except Exception as ws_error:
                    print(f"WebSocket notification error (non-fatal): {ws_error}")

        except Exception as e:
            print(f"Create notification error: {e}")

    def get_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> Dict[str, Any]:
        """Get notifications for a user"""
        try:
            if not self.supabase:
                return {'success': True, 'notifications': [], 'unread_count': 0}

            query = (
                self.supabase.table('notifications')
                .select('*, actor:users!actor_id(id, username, avatar_url), post:posts!post_id(id, content)')
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .limit(limit)
            )

            if unread_only:
                query = query.eq('is_read', False)

            result = query.execute()

            # Get unread count
            unread = (
                self.supabase.table('notifications')
                .select('id', count='exact')
                .eq('user_id', user_id)
                .eq('is_read', False)
                .execute()
            )

            return {
                'success': True,
                'notifications': result.data or [],
                'unread_count': unread.count if unread.count else 0,
            }

        except Exception as e:
            print(f"Get notifications error: {e}")
            return {'success': False, 'error': str(e), 'notifications': [], 'unread_count': 0}

    def mark_notification_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Mark a notification as read"""
        try:
            if not self.supabase:
                return {'success': True}

            self.supabase.table('notifications').update({'is_read': True}).eq('id', notification_id).eq(
                'user_id', user_id
            ).execute()

            return {'success': True, 'message': 'Notification marked as read'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def mark_all_notifications_read(self, user_id: str) -> Dict[str, Any]:
        """Mark all notifications as read for a user"""
        try:
            if not self.supabase:
                return {'success': True}

            self.supabase.table('notifications').update({'is_read': True}).eq('user_id', user_id).eq(
                'is_read', False
            ).execute()

            return {'success': True, 'message': 'All notifications marked as read'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ==================== PHASE 2: REPORTS & BLOCKS ====================

    def report_content(
        self,
        reporter_id: str,
        reason: str,
        description: Optional[str] = None,
        reported_user_id: Optional[str] = None,
        post_id: Optional[str] = None,
        comment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Report inappropriate content"""
        try:
            if not self.supabase:
                return {'success': True, 'message': 'Report submitted'}

            if not any([reported_user_id, post_id, comment_id]):
                return {'success': False, 'error': 'Must specify content to report'}

            self.supabase.table('reports').insert(
                {
                    'reporter_id': reporter_id,
                    'reported_user_id': reported_user_id,
                    'post_id': post_id,
                    'comment_id': comment_id,
                    'reason': reason,
                    'description': description,
                    'status': 'pending',
                    'created_at': datetime.utcnow().isoformat(),
                }
            ).execute()

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

            existing = (
                self.supabase.table('user_blocks')
                .select('id')
                .eq('blocker_id', blocker_id)
                .eq('blocked_id', blocked_id)
                .execute()
            )

            if existing.data:
                # Unblock
                self.supabase.table('user_blocks').delete().eq('blocker_id', blocker_id).eq(
                    'blocked_id', blocked_id
                ).execute()
                return {'success': True, 'blocked': False, 'message': 'User unblocked'}
            else:
                # Block - also unfollow if following
                self.supabase.table('user_blocks').insert(
                    {'blocker_id': blocker_id, 'blocked_id': blocked_id, 'created_at': datetime.utcnow().isoformat()}
                ).execute()

                # Remove any existing follow relationship
                self.supabase.table('user_follows').delete().eq('follower_id', blocker_id).eq(
                    'following_id', blocked_id
                ).execute()
                self.supabase.table('user_follows').delete().eq('follower_id', blocked_id).eq(
                    'following_id', blocker_id
                ).execute()

                return {'success': True, 'blocked': True, 'message': 'User blocked'}

        except Exception as e:
            print(f"Toggle block error: {e}")
            return {'success': False, 'error': str(e)}

    def _is_blocked(self, user_id: str, other_user_id: str) -> bool:
        """Check if users have blocked each other"""
        try:
            if not self.supabase:
                return False
            result = (
                self.supabase.table('user_blocks')
                .select('id')
                .or_(f"blocker_id.eq.{user_id},blocker_id.eq.{other_user_id}")
                .or_(f"blocked_id.eq.{user_id},blocked_id.eq.{other_user_id}")
                .execute()
            )
            return bool(result.data)
        except Exception:
            return False

    def get_blocked_users(self, user_id: str) -> Dict[str, Any]:
        """Get list of users blocked by current user"""
        try:
            if not self.supabase:
                return {'success': True, 'users': []}

            result = (
                self.supabase.table('user_blocks')
                .select('*, users!blocked_id(id, username, avatar_url)')
                .eq('blocker_id', user_id)
                .execute()
            )

            users = [b.get('users') for b in (result.data or []) if b.get('users')]
            return {'success': True, 'users': users}

        except Exception as e:
            return {'success': False, 'error': str(e), 'users': []}

    # ==================== PHASE 3: ADMIN MODERATION ====================

    def is_admin(self, user_id: str) -> bool:
        """Check if a user is an admin"""
        try:
            if not self.supabase:
                return False

            result = self.supabase.table('users').select('is_admin').eq('id', user_id).single().execute()

            return result.data.get('is_admin', False) if result.data else False

        except Exception as e:
            print(f"Check admin error: {e}")
            return False

    def get_all_reports(self, status: str = 'pending', limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get all reports for admin moderation"""
        try:
            if not self.supabase:
                return {'success': True, 'reports': [], 'count': 0}

            query = (
                self.supabase.table('reports')
                .select('''
                    *,
                    reporter:users!reporter_id(id, username, avatar_url),
                    reported_user:users!reported_user_id(id, username, avatar_url),
                    post:posts!post_id(id, content, user_id),
                    comment:post_comments!comment_id(id, content, user_id)
                ''')
                .order('created_at', desc=True)
                .range(offset, offset + limit - 1)
            )

            if status != 'all':
                query = query.eq('status', status)

            result = query.execute()

            return {'success': True, 'reports': result.data or [], 'count': len(result.data) if result.data else 0}

        except Exception as e:
            print(f"Get all reports error: {e}")
            return {'success': False, 'error': str(e), 'reports': []}

    def handle_report(self, report_id: str, admin_id: str, action: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Handle a report with the specified action"""
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Database not configured'}

            # Get the report
            report = self.supabase.table('reports').select('*').eq('id', report_id).single().execute()

            if not report.data:
                return {'success': False, 'error': 'Report not found'}

            report_data = report.data

            # Handle based on action
            if action == 'dismiss':
                # Just update status
                self.supabase.table('reports').update(
                    {
                        'status': 'dismissed',
                        'reviewed_by': admin_id,
                        'reviewed_at': datetime.utcnow().isoformat(),
                        'admin_notes': notes,
                    }
                ).eq('id', report_id).execute()

            elif action == 'delete_content':
                # Delete the reported content
                if report_data.get('post_id'):
                    self.delete_post(report_data['post_id'])
                elif report_data.get('comment_id'):
                    self._delete_comment_admin(report_data['comment_id'])

                self.supabase.table('reports').update(
                    {
                        'status': 'resolved',
                        'reviewed_by': admin_id,
                        'reviewed_at': datetime.utcnow().isoformat(),
                        'admin_notes': notes,
                        'action_taken': 'content_deleted',
                    }
                ).eq('id', report_id).execute()

            elif action == 'warn_user':
                # Create a warning notification
                reported_user_id = report_data.get('reported_user_id')
                if reported_user_id:
                    self._create_notification(
                        user_id=reported_user_id,
                        type='warning',
                        content=notes or 'You have received a warning for violating community guidelines.',
                    )

                self.supabase.table('reports').update(
                    {
                        'status': 'resolved',
                        'reviewed_by': admin_id,
                        'reviewed_at': datetime.utcnow().isoformat(),
                        'admin_notes': notes,
                        'action_taken': 'user_warned',
                    }
                ).eq('id', report_id).execute()

            elif action == 'ban_user':
                # Ban the user
                reported_user_id = report_data.get('reported_user_id')
                if reported_user_id:
                    self.supabase.table('users').update(
                        {
                            'is_banned': True,
                            'banned_at': datetime.utcnow().isoformat(),
                            'banned_by': admin_id,
                            'ban_reason': notes,
                        }
                    ).eq('id', reported_user_id).execute()

                self.supabase.table('reports').update(
                    {
                        'status': 'resolved',
                        'reviewed_by': admin_id,
                        'reviewed_at': datetime.utcnow().isoformat(),
                        'admin_notes': notes,
                        'action_taken': 'user_banned',
                    }
                ).eq('id', report_id).execute()

            return {'success': True, 'message': f'Report {action} successfully'}

        except Exception as e:
            print(f"Handle report error: {e}")
            return {'success': False, 'error': str(e)}

    def _delete_comment_admin(self, comment_id: str) -> bool:
        """Delete a comment (admin action)"""
        try:
            if not self.supabase:
                return False

            self.supabase.table('post_comments').delete().eq('id', comment_id).execute()
            return True
        except Exception:
            return False

    def get_moderation_stats(self) -> Dict[str, Any]:
        """Get moderation statistics"""
        try:
            if not self.supabase:
                return {'success': True, 'stats': {}}

            # Get counts by status
            pending = self.supabase.table('reports').select('id', count='exact').eq('status', 'pending').execute()

            resolved = self.supabase.table('reports').select('id', count='exact').eq('status', 'resolved').execute()

            dismissed = self.supabase.table('reports').select('id', count='exact').eq('status', 'dismissed').execute()

            # Get user stats
            total_users = self.supabase.table('users').select('id', count='exact').execute()

            banned_users = self.supabase.table('users').select('id', count='exact').eq('is_banned', True).execute()

            # Get post stats
            total_posts = self.supabase.table('posts').select('id', count='exact').execute()

            return {
                'success': True,
                'stats': {
                    'reports': {
                        'pending': pending.count or 0,
                        'resolved': resolved.count or 0,
                        'dismissed': dismissed.count or 0,
                        'total': (pending.count or 0) + (resolved.count or 0) + (dismissed.count or 0),
                    },
                    'users': {'total': total_users.count or 0, 'banned': banned_users.count or 0},
                    'posts': {'total': total_posts.count or 0},
                },
            }

        except Exception as e:
            print(f"Get moderation stats error: {e}")
            return {'success': False, 'error': str(e)}
