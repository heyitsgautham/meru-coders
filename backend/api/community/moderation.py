"""Community moderation: user reports and the admin review routes."""

from flask import current_app, jsonify, request

from ...auth.middleware import require_auth
from . import community_bp, community_model

# ==================== PHASE 2: REPORTS & BLOCKS ====================


@community_bp.route('/reports', methods=['POST'])
@require_auth
def report_content(current_user):
    """Report inappropriate content"""
    try:
        data = request.get_json()
        if not data.get('reason'):
            return jsonify({'success': False, 'error': 'Reason is required'}), 400

        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        result = community_model.report_content(
            reporter_id=user_id,
            reason=data['reason'],
            description=data.get('description'),
            reported_user_id=data.get('user_id'),
            post_id=data.get('post_id'),
            comment_id=data.get('comment_id'),
        )
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PHASE 3: ADMIN MODERATION ====================


@community_bp.route('/admin/reports', methods=['GET'])
@require_auth
def get_all_reports(current_user):
    """
    Get all reports for admin moderation
    Requires admin privileges
    """
    try:
        # Check if user is admin
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        if not community_model.is_admin(user_id):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403

        status = request.args.get('status', 'pending')  # pending, reviewed, dismissed
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)

        result = community_model.get_all_reports(status=status, limit=limit, offset=offset)
        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        current_app.logger.error(f"Get reports error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/admin/reports/<report_id>/action', methods=['POST'])
@require_auth
def take_report_action(current_user, report_id):
    """
    Take action on a report (dismiss, warn user, delete content, ban user)
    Requires admin privileges
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        if not community_model.is_admin(user_id):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403

        data = request.get_json()
        action = data.get('action')  # dismiss, delete_content, warn_user, ban_user

        if action not in ['dismiss', 'delete_content', 'warn_user', 'ban_user']:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400

        result = community_model.handle_report(
            report_id=report_id, admin_id=user_id, action=action, notes=data.get('notes')
        )
        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        current_app.logger.error(f"Report action error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@community_bp.route('/admin/stats', methods=['GET'])
@require_auth
def get_moderation_stats(current_user):
    """Get moderation statistics"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user.get('id')
        if not community_model.is_admin(user_id):
            return jsonify({'success': False, 'error': 'Admin access required'}), 403

        result = community_model.get_moderation_stats()
        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
