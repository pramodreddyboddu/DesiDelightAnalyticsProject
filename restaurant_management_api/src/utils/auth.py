from functools import wraps
from flask import session, jsonify, current_app, request
from ..models.user import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not session.get('user_id'):
                current_app.logger.warning('Login required check - No user_id in session')
                return jsonify({'error': 'Authentication required'}), 401

            user = User.query.get(session['user_id'])
            if not user:
                current_app.logger.warning('Login required check - User not found in database')
                session.clear()
                return jsonify({'error': 'User not found'}), 401

            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Login required check error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not session.get('user_id'):
                current_app.logger.warning('Admin required check - No user_id in session')
                return jsonify({'error': 'Authentication required'}), 401

            user = User.query.get(session['user_id'])
            if not user:
                current_app.logger.warning('Admin required check - User not found in database')
                session.clear()
                return jsonify({'error': 'User not found'}), 401

            if not user.is_admin:
                current_app.logger.warning('Admin required check - User is not an admin')
                return jsonify({'error': 'Admin privileges required'}), 403

            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Admin required check error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return decorated_function 