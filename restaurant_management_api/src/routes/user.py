from flask import Blueprint, jsonify, request, session, current_app
from src.models.user import User, db
from src.utils.auth import admin_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Deletes a user, ensuring admins can only delete users within their own tenant."""
    try:
        requesting_user_id = session.get('user_id')
        requesting_user = User.query.get(requesting_user_id)

        user_to_delete = User.query.get(user_id)

        if not user_to_delete:
            return jsonify({'error': 'User not found'}), 404

        # Prevent users from deleting themselves
        if requesting_user.id == user_to_delete.id:
            return jsonify({'error': 'You cannot delete your own account'}), 403

        # Super admins can delete any user except themselves.
        # Tenant admins can only delete users within their own tenant.
        is_super_admin = requesting_user.is_admin and not requesting_user.tenant_id
        if not is_super_admin and requesting_user.tenant_id != user_to_delete.tenant_id:
            return jsonify({'error': 'You can only delete users from your own tenant'}), 403

        db.session.delete(user_to_delete)
        db.session.commit()

        current_app.logger.info(f"User '{requesting_user.username}' deleted user '{user_to_delete.username}'.")

        return jsonify({'message': f'User {user_to_delete.username} has been deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
