from flask import Blueprint, request, jsonify, session, current_app, make_response
from ..models import db
from ..models.user import User
from ..utils.auth import login_required, admin_required
from werkzeug.security import check_password_hash, generate_password_hash
import os
import pickle
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Set user in session
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['is_admin'] = user.is_admin

        # Only log successful login
        current_app.logger.warning(f'User {username} logged in successfully')

        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'is_admin': user.is_admin
            }
        })
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout"""
    try:
        # Log session details before logout
        current_app.logger.info('Before logout - Session: %s', dict(session))
        current_app.logger.info('Before logout - Session ID: %s', session.sid if hasattr(session, 'sid') else 'No session ID')
        current_app.logger.info('Before logout - Session Cookie: %s', request.cookies.get('session'))

        # Clear session
        session.clear()

        # Log session details after logout
        current_app.logger.info('After logout - Session: %s', dict(session))
        current_app.logger.info('After logout - Session ID: %s', session.sid if hasattr(session, 'sid') else 'No session ID')
        current_app.logger.info('After logout - Session Cookie: %s', request.cookies.get('session'))

        return jsonify({'message': 'Logout successful'})
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'No user in session'}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'is_admin': user.is_admin
        })
    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
@admin_required
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        user = User(
            username=username,
            email=email,
            role=role,
            is_admin=(role == 'admin')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_admin': user.is_admin
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in register endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/test-session', methods=['GET'])
def test_session():
    """Test session handling"""
    try:
        # Log current session state
        current_app.logger.info('Current session: %s', dict(session))
        current_app.logger.info('Session ID: %s', session.sid if hasattr(session, 'sid') else 'No session ID')
        current_app.logger.info('Request cookies: %s', dict(request.cookies))

        # Set a test value in the session
        session['test_value'] = 'test123'
        session.modified = True

        # Log session after modification
        current_app.logger.info('Session after modification: %s', dict(session))

        return jsonify({
            'message': 'Session test successful',
            'session_id': session.sid if hasattr(session, 'sid') else 'No session ID',
            'session_data': dict(session)
        })
    except Exception as e:
        current_app.logger.error(f"Session test error: {str(e)}")
        return jsonify({'error': str(e)}), 500

