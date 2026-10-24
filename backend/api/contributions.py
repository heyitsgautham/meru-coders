"""
Contribution API routes.
Handles user submissions and admin approval workflow.
"""

from flask import Blueprint, current_app, jsonify, request

from backend.auth import require_admin, require_auth
from backend.models import (
    approve_contribution,
    get_pending_contributions,
    get_user_contributions,
    reject_contribution,
    submit_contribution,
)

contrib_bp = Blueprint('contributions', __name__, url_prefix='/api/contributions')


@contrib_bp.route('/submit', methods=['POST'])
@require_auth
def submit():
    """
    Submit a new contribution (verse or meter definition).
    Requires authentication.
    """
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        contribution_type = data.get('type')  # 'verse' or 'meter_definition'
        contribution_data = data.get('data', {})

        if contribution_type not in ['verse', 'meter_definition']:
            return jsonify({
                'success': False,
                'error': 'Invalid contribution type',
                'message': 'Type must be "verse" or "meter_definition"'
            }), 400

        # Validate verse data
        if contribution_type == 'verse':
            if not contribution_data.get('verse_text') or not contribution_data.get('meter'):
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields',
                    'message': 'Verse text and meter are required'
                }), 400

        # Validate meter definition data
        if contribution_type == 'meter_definition':
            if not contribution_data.get('meter_name_devanagari'):
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields',
                    'message': 'Meter name is required'
                }), 400

        # Submit contribution
        result = submit_contribution(
            user_id=user.id,
            contribution_type=contribution_type,
            data=contribution_data
        )

        if result:
            return jsonify({
                'success': True,
                'message': 'Contribution submitted successfully',
                'contribution': result
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Submission failed',
                'message': 'Could not save contribution'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Submit contribution error: {e}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@contrib_bp.route('/my-contributions', methods=['GET'])
@require_auth
def my_contributions():
    """
    Get all contributions submitted by current user.
    Requires authentication.
    """
    try:
        user = request.current_user
        status = request.args.get('status')  # Optional: 'pending', 'approved', 'rejected'

        contributions = get_user_contributions(user.id, status)

        return jsonify({
            'success': True,
            'contributions': contributions,
            'count': len(contributions)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get my contributions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@contrib_bp.route('/admin/pending', methods=['GET'])
@require_admin
def admin_get_pending():
    """
    Get all pending contributions for admin review.
    Requires admin privileges.
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        contributions = get_pending_contributions(limit, offset)

        return jsonify({
            'success': True,
            'contributions': contributions,
            'count': len(contributions),
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get pending contributions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@contrib_bp.route('/admin/approve/<contribution_id>', methods=['POST'])
@require_admin
def admin_approve(contribution_id):
    """
    Approve a contribution and move it to the appropriate table.
    Requires admin privileges.
    """
    try:
        user = request.current_user
        data = request.get_json() or {}
        notes = data.get('notes')

        success = approve_contribution(contribution_id, user.id, notes)

        if success:
            return jsonify({
                'success': True,
                'message': 'Contribution approved successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Approval failed',
                'message': 'Could not approve contribution'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Approve contribution error: {e}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@contrib_bp.route('/admin/reject/<contribution_id>', methods=['POST'])
@require_admin
def admin_reject(contribution_id):
    """
    Reject a contribution with optional notes.
    Requires admin privileges.
    """
    try:
        user = request.current_user
        data = request.get_json() or {}
        notes = data.get('notes')

        success = reject_contribution(contribution_id, user.id, notes)

        if success:
            return jsonify({
                'success': True,
                'message': 'Contribution rejected'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Rejection failed',
                'message': 'Could not reject contribution'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Reject contribution error: {e}")
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500
