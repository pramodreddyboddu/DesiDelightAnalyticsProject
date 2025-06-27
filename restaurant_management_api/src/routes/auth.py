from flask import Blueprint, request, jsonify, session, current_app, make_response
from ..models import db
from ..models.user import User
from ..utils.auth import login_required, admin_required
from werkzeug.security import check_password_hash, generate_password_hash
import os
import pickle
import logging
from datetime import datetime, timedelta

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
        session['tenant_id'] = user.tenant_id

        # Debug: log session after login
        current_app.logger.info(f"Session after login: {dict(session)}")

        # Only log successful login
        current_app.logger.warning(f'User {username} logged in successfully')

        resp = make_response(jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }))
        # Debug: print response headers
        print('Login response headers:', dict(resp.headers))
        return resp
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
        current_app.logger.info(f"Session in /me: {dict(session)}")
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'No user in session'}), 401

        user = User.query.get(user_id)
        if not user:
            # If user not found, clear the invalid session
            session.clear()
            return jsonify({'error': 'User not found in database'}), 404

        # Ensure session is up-to-date with DB
        session['tenant_id'] = user.tenant_id
        session['is_admin'] = user.is_admin

        return jsonify({'user': user.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
@admin_required
def register():
    """Creates a new user, scoped to the requesting admin's tenant if applicable."""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Get the admin user who is creating this new user
        requesting_user_id = session.get('user_id')
        requesting_user = User.query.get(requesting_user_id)
        
        # New user should belong to the same tenant as the admin creating them
        tenant_id = requesting_user.tenant_id

        # Check for username collision ONLY within the same tenant
        existing_user = User.query.filter_by(username=username, tenant_id=tenant_id).first()
        if existing_user:
            return jsonify({'error': f"Username '{username}' already exists in this tenant"}), 400
        
        user = User(
            username=username,
            email=email,
            role=role,
            is_admin=(role == 'admin'),
            tenant_id=tenant_id  # Assign the tenant_id from the creator
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f"Admin '{requesting_user.username}' created new user '{user.username}' for tenant '{tenant_id}'.")
        
        return jsonify(user.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in register endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/test-session', methods=['GET'])
def test_session():
    session['test'] = 'hello'
    current_app.logger.info(f"Session in test-session: {dict(session)}")
    return jsonify({'session': dict(session)})

