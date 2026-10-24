"""
Contribution model for handling user submissions
"""

from datetime import datetime

from supabase import create_client

from ..config.settings import settings


class ContributionModel:
    """Handle user contributions and admin approval workflow"""

    def __init__(self):
        # Create client lazily to avoid crashes when env vars are missing during startup
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        else:
            self.supabase = None

    def submit_contribution(self, user_id, contribution_type, data):
        """
        Submit a new contribution

        Args:
            user_id: User ID from auth
            contribution_type: 'verse' or 'meter_definition'
            data: Dict containing the contribution data

        Returns:
            Dict with success status and contribution ID
        """
        try:
            if not self.supabase:
                # Dev fallback: accept and echo success without persisting
                return {
                    'success': True,
                    'contribution_id': f"local-{user_id}",
                    'message': 'Contribution accepted (local dev fallback)',
                }
            contribution = {
                'contribution_type': contribution_type,
                'data': data,
                'status': 'pending',
                'submitted_by': user_id,
                'submitted_at': datetime.utcnow().isoformat(),
            }

            result = self.supabase.table('pending_contributions').insert(contribution).execute()

            if result.data:
                return {
                    'success': True,
                    'contribution_id': result.data[0]['id'],
                    'message': 'Contribution submitted successfully',
                }
            else:
                return {'success': False, 'error': 'Failed to submit contribution'}

        except Exception as e:
            print(f"Submit contribution error: {e}")
            return {'success': False, 'error': str(e)}

    def get_pending_contributions(self, limit=50, offset=0):
        """
        Get all pending contributions for admin review

        Args:
            limit: Number of results to return
            offset: Pagination offset

        Returns:
            List of pending contributions
        """
        try:
            if not self.supabase:
                return {
                    'success': False,
                    'error': 'Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.',
                    'contributions': [],
                }
            result = (
                self.supabase.table('pending_contributions')
                .select('*, users!submitted_by(username)')
                .eq('status', 'pending')
                .order('submitted_at', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return {
                'success': True,
                'contributions': result.data or [],
                'count': len(result.data) if result.data else 0,
            }

        except Exception as e:
            print(f"Get pending contributions error: {e}")
            return {'success': False, 'error': str(e), 'contributions': []}

    def approve_contribution(self, contribution_id, admin_id, review_notes=None):
        """
        Approve a contribution and move to approved_contributions table

        Args:
            contribution_id: ID of contribution to approve
            admin_id: Admin user ID
            review_notes: Optional notes from admin

        Returns:
            Dict with success status
        """
        try:
            if not self.supabase:
                return {'success': True, 'message': 'Contribution approved (local dev fallback)'}
            # Get the contribution
            contribution = (
                self.supabase.table('pending_contributions').select('*').eq('id', contribution_id).single().execute()
            )

            if not contribution.data:
                return {'success': False, 'error': 'Contribution not found'}

            contrib_data = contribution.data

            # Move to approved_contributions table
            reviewed_by = admin_id if (self.supabase and self._valid_reviewer_id(admin_id)) else None
            approved_data = {
                'contribution_type': contrib_data['contribution_type'],
                'data': contrib_data['data'],
                'status': 'approved',
                'submitted_by': contrib_data['submitted_by'],
                'reviewed_by': reviewed_by,
                'review_notes': review_notes,
                'submitted_at': contrib_data['submitted_at'],
                'reviewed_at': datetime.utcnow().isoformat(),
            }

            # Insert into approved_contributions
            self.supabase.table('approved_contributions').insert(approved_data).execute()

            # Update pending contribution status
            self.supabase.table('pending_contributions').update(
                {
                    'status': 'approved',
                    'reviewed_by': reviewed_by,
                    'reviewed_at': datetime.utcnow().isoformat(),
                    'review_notes': review_notes,
                }
            ).eq('id', contribution_id).execute()

            return {'success': True, 'message': 'Contribution approved successfully'}

        except Exception as e:
            print(f"Approve contribution error: {e}")
            return {'success': False, 'error': str(e)}

    def reject_contribution(self, contribution_id, admin_id, review_notes=None):
        """
        Reject a contribution

        Args:
            contribution_id: ID of contribution to reject
            admin_id: Admin user ID
            review_notes: Optional notes from admin

        Returns:
            Dict with success status
        """
        try:
            if not self.supabase:
                return {'success': True, 'message': 'Contribution rejected (local dev fallback)'}
            reviewed_by = admin_id if (self.supabase and self._valid_reviewer_id(admin_id)) else None
            result = (
                self.supabase.table('pending_contributions')
                .update(
                    {
                        'status': 'rejected',
                        'reviewed_by': reviewed_by,
                        'reviewed_at': datetime.utcnow().isoformat(),
                        'review_notes': review_notes,
                    }
                )
                .eq('id', contribution_id)
                .execute()
            )

            if result.data:
                return {'success': True, 'message': 'Contribution rejected'}
            else:
                return {'success': False, 'error': 'Failed to reject contribution'}

        except Exception as e:
            print(f"Reject contribution error: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _is_uuid(value):
        import uuid

        try:
            uuid.UUID(str(value))
            return True
        except Exception:
            return False

    def _valid_reviewer_id(self, admin_id):
        """Return True only if admin_id is a UUID that exists in Supabase users table."""
        if not admin_id or not self._is_uuid(admin_id):
            return False
        try:
            result = self.supabase.table('users').select('id').eq('id', admin_id).execute()
            return bool(result.data and len(result.data) > 0)
        except Exception:
            return False

    def get_user_contributions(self, user_id, limit=50, offset=0):
        """
        Get all contributions by a specific user (pending, approved, and rejected)

        Args:
            user_id: User ID
            limit: Number of results
            offset: Pagination offset

        Returns:
            List of user's contributions from all statuses
        """
        try:
            if not self.supabase:
                return {
                    'success': False,
                    'error': 'Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY.',
                    'contributions': [],
                }

            # Get all pending contributions (including rejected ones)
            pending_result = (
                self.supabase.table('pending_contributions')
                .select('*')
                .eq('submitted_by', user_id)
                .order('submitted_at', desc=True)
                .execute()
            )

            # Get all approved contributions
            approved_result = (
                self.supabase.table('approved_contributions')
                .select('*')
                .eq('submitted_by', user_id)
                .order('reviewed_at', desc=True)
                .execute()
            )

            # Combine and sort by most recent
            all_contributions = []

            if pending_result.data:
                all_contributions.extend(pending_result.data)

            if approved_result.data:
                all_contributions.extend(approved_result.data)

            # Sort by created/reviewed date (most recent first)
            all_contributions.sort(key=lambda x: x.get('reviewed_at') or x.get('submitted_at') or '', reverse=True)

            # Apply pagination
            paginated = all_contributions[offset : offset + limit]

            return {'success': True, 'contributions': paginated, 'count': len(all_contributions)}

        except Exception as e:
            print(f"Get user contributions error: {e}")
            return {'success': False, 'error': str(e), 'contributions': []}

    def get_approved_contributions(self, limit=100, offset=0, contribution_type=None):
        """
        Get all approved contributions for display in datasets page

        Args:
            limit: Number of results to return
            offset: Pagination offset
            contribution_type: Filter by type ('verse' or 'meter_definition')

        Returns:
            Dict with approved contributions
        """
        try:
            if not self.supabase:
                return {
                    'success': True,
                    'contributions': [],
                    'count': 0,
                    'message': 'Supabase not configured (dev fallback)',
                }

            query = (
                self.supabase.table('approved_contributions')
                .select('*, submitted_by(*)', count='exact')
                .eq('status', 'approved')
                .order('reviewed_at', desc=True)
            )

            if contribution_type:
                query = query.eq('contribution_type', contribution_type)

            result = query.range(offset, offset + limit - 1).execute()

            return {'success': True, 'contributions': result.data or [], 'count': result.count or 0}

        except Exception as e:
            print(f"Get approved contributions error: {e}")
            return {'success': False, 'error': str(e), 'contributions': [], 'count': 0}
