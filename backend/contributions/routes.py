"""
Contributions API Routes
Handles user submissions of verses and meter definitions
"""
from flask import Blueprint, request, jsonify
from ..auth.middleware import require_auth, require_admin
from ..models.contribution import ContributionModel

contributions_bp = Blueprint('contributions', __name__)
# Alias for backward compatibility with previous import name
contribution_bp = contributions_bp
contribution_model = ContributionModel()


@contributions_bp.route('/submit', methods=['POST'])
@require_auth
def submit_contribution(current_user):
    """Submit a new contribution (verse or meter definition)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'contribution_type' not in data or 'data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: contribution_type and data'
            }), 400
        
        contribution_type = data['contribution_type']
        contribution_data = data['data']
        
        # Validate contribution type
        if contribution_type not in ['verse', 'meter_definition']:
            return jsonify({
                'success': False,
                'error': 'Invalid contribution_type. Must be "verse" or "meter_definition"'
            }), 400
        
        # Create contribution via Supabase
        result = contribution_model.submit_contribution(
            user_id=current_user['id'],
            contribution_type=contribution_type,
            data=contribution_data
        )

        status_code = 201 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@contributions_bp.route('/my-contributions', methods=['GET'])
@require_auth
def get_my_contributions(current_user):
    """Get all contributions by the current user"""
    try:
        result = contribution_model.get_user_contributions(current_user['id'])
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Admin routes
@contributions_bp.route('/admin/pending', methods=['GET'])
@require_admin
def get_pending_contributions(current_user):
    """Get all pending contributions (Admin only)"""
    try:
        result = contribution_model.get_pending_contributions()
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@contributions_bp.route('/admin/approve/<contribution_id>', methods=['POST'])
@require_admin
def approve_contribution(current_user, contribution_id):
    """Approve a contribution (Admin only)"""
    try:
        # Allow empty bodies from simple POSTs by suppressing strict content-type checks
        data = request.get_json(silent=True) or {}
        review_notes = data.get('review_notes', '')
        
        result = contribution_model.approve_contribution(
            contribution_id=contribution_id,
            admin_id=current_user['id'],
            review_notes=review_notes
        )

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@contributions_bp.route('/admin/reject/<contribution_id>', methods=['POST'])
@require_admin
def reject_contribution(current_user, contribution_id):
    """Reject a contribution (Admin only)"""
    try:
        # Allow empty bodies from simple POSTs by suppressing strict content-type checks
        data = request.get_json(silent=True) or {}
        review_notes = data.get('review_notes', '')
        
        result = contribution_model.reject_contribution(
            contribution_id=contribution_id,
            admin_id=current_user['id'],
            review_notes=review_notes
        )

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@contributions_bp.route('/approved', methods=['GET'])
def get_approved_contributions():
    """Get all approved contributions for datasets page (Public endpoint)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        contribution_type = request.args.get('type', None)
        
        result = contribution_model.get_approved_contributions(
            limit=limit,
            offset=offset,
            contribution_type=contribution_type
        )
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
