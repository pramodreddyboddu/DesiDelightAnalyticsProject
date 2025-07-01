from flask import Blueprint, request, jsonify, session, current_app, make_response
from ..models import db
from ..models.user import User
from ..models.chef import Chef
from ..models.item import Item
from ..models.chef_dish_mapping import ChefDishMapping
from ..utils.auth import login_required, admin_required
from werkzeug.security import check_password_hash, generate_password_hash
import os
import pickle
import logging
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

def sync_chef_mappings_for_tenant(tenant_id):
    """Helper function to sync chef mappings for a tenant"""
    try:
        if not tenant_id:
            current_app.logger.warning("No tenant_id provided for chef mapping sync")
            return {'status': 'skipped', 'reason': 'no_tenant_id'}

        # Ensure 'Unassigned' chef exists for this tenant
        unassigned_chef = Chef.query.filter_by(name='Unassigned', tenant_id=tenant_id).first()
        if not unassigned_chef:
            unassigned_chef = Chef(clover_id=f'unassigned_{tenant_id}', name='Unassigned', is_active=True, tenant_id=tenant_id)
            db.session.add(unassigned_chef)
            db.session.commit()
            current_app.logger.info(f"Created 'Unassigned' chef for tenant {tenant_id}")

        # Find all items for this tenant not mapped in ChefDishMapping
        mapped_item_ids = set(m.item_id for m in ChefDishMapping.query.filter_by(tenant_id=tenant_id).all())
        unmapped_items = Item.query.filter(Item.tenant_id==tenant_id, ~Item.id.in_(mapped_item_ids)).all()

        created_count = 0
        for item in unmapped_items:
            mapping = ChefDishMapping(chef_id=unassigned_chef.id, item_id=item.id, is_active=True, tenant_id=tenant_id)
            db.session.add(mapping)
            created_count += 1
        
        if created_count > 0:
            db.session.commit()
            current_app.logger.info(f"Auto-synced {created_count} chef mappings for tenant {tenant_id}")
        else:
            current_app.logger.debug(f"No new chef mappings needed for tenant {tenant_id}")

        return {
            'status': 'success',
            'created_mappings': created_count,
            'unassigned_chef_id': unassigned_chef.id,
            'tenant_id': tenant_id
        }
    except Exception as e:
        current_app.logger.error(f"Error in auto chef mapping sync for tenant {tenant_id}: {str(e)}")
        db.session.rollback()
        return {'status': 'error', 'error': str(e)}

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

        # Check if this is a mobile request
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
        
        if is_mobile:
            current_app.logger.warning(f'Mobile browser using regular login endpoint: {user_agent}')
        else:
            current_app.logger.info(f'Desktop browser login: {user_agent}')

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

        # Auto-sync chef mappings for the tenant (non-blocking)
        if user.tenant_id:
            try:
                sync_result = sync_chef_mappings_for_tenant(user.tenant_id)
                current_app.logger.info(f"Auto chef mapping sync result: {sync_result}")
            except Exception as sync_error:
                current_app.logger.error(f"Auto chef mapping sync failed: {str(sync_error)}")
                # Don't fail login if sync fails

        # Only log successful login
        current_app.logger.warning(f'User {username} logged in successfully')

        resp = make_response(jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }))
        
        # Mobile browser detection and session cookie adjustment
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
        
        if is_mobile:
            # For mobile browsers, try multiple cookie strategies
            current_app.logger.info(f"Mobile browser detected for user {username}")
            
            # Strategy 1: Try with SameSite=None (most permissive)
            resp.set_cookie(
                'plateiq_session',
                session.sid if hasattr(session, 'sid') else '',
                secure=True,
                httponly=True,
                samesite='None',  # Most permissive for cross-origin
                path='/',
                max_age=86400  # 1 day
            )
            
            # Strategy 2: Also set a non-httponly cookie for mobile debugging
            resp.set_cookie(
                'plateiq_session_debug',
                'mobile_session_active',
                secure=True,
                httponly=False,  # Allow JavaScript access
                samesite='None',
                path='/',
                max_age=86400
            )
            
            # Strategy 3: Set additional mobile-specific cookies
            resp.set_cookie(
                'plateiq_mobile_debug',
                'logged_in',
                secure=True,
                httponly=False,
                samesite='None',
                path='/',
                max_age=86400
            )
            
            current_app.logger.info(f"Mobile session cookies set for user {username}")
        else:
            # For desktop browsers, use standard settings
            current_app.logger.info(f"Desktop browser detected for user {username}")
        
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
        # Debug: log request headers and cookies
        print(f"/me request headers: {dict(request.headers)}")
        print(f"/me request cookies: {request.cookies}")
        current_app.logger.warning(f"/me request headers: {dict(request.headers)}")
        current_app.logger.warning(f"/me request cookies: {request.cookies}")
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

@auth_bp.route('/session-info', methods=['GET'])
def session_info():
    """Get detailed session information for debugging"""
    return jsonify({
        'session_exists': bool(session),
        'session_data': dict(session),
        'session_id': session.sid if hasattr(session, 'sid') else 'No session ID',
        'cookies': dict(request.cookies),
        'headers': {
            'origin': request.headers.get('Origin'),
            'referer': request.headers.get('Referer'),
            'user_agent': request.headers.get('User-Agent')
        }
    })

@auth_bp.route('/session-debug', methods=['GET'])
def session_debug():
    """Comprehensive session debugging endpoint"""
    from flask import current_app
    
    # Get session configuration
    session_config = {
        'type': current_app.config.get('SESSION_TYPE'),
        'secure': current_app.config.get('SESSION_COOKIE_SECURE'),
        'samesite': current_app.config.get('SESSION_COOKIE_SAMESITE'),
        'httponly': current_app.config.get('SESSION_COOKIE_HTTPONLY'),
        'name': current_app.config.get('SESSION_COOKIE_NAME'),
        'path': current_app.config.get('SESSION_COOKIE_PATH'),
        'domain': current_app.config.get('SESSION_COOKIE_DOMAIN'),
        'permanent': current_app.config.get('SESSION_PERMANENT'),
        'lifetime': str(current_app.config.get('PERMANENT_SESSION_LIFETIME')),
        'refresh_each_request': current_app.config.get('SESSION_REFRESH_EACH_REQUEST'),
        'use_signer': current_app.config.get('SESSION_USE_SIGNER'),
        'key_prefix': current_app.config.get('SESSION_KEY_PREFIX')
    }
    
    # Get request information
    request_info = {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'cookies': dict(request.cookies),
        'origin': request.headers.get('Origin'),
        'referer': request.headers.get('Referer'),
        'user_agent': request.headers.get('User-Agent')
    }
    
    # Get session information
    session_info = {
        'exists': bool(session),
        'data': dict(session),
        'id': session.sid if hasattr(session, 'sid') else 'No session ID',
        'permanent': session.permanent if hasattr(session, 'permanent') else 'Unknown',
        'modified': session.modified if hasattr(session, 'modified') else 'Unknown'
    }
    
    return jsonify({
        'session_config': session_config,
        'request_info': request_info,
        'session_info': session_info,
        'timestamp': datetime.utcnow().isoformat()
    })

@auth_bp.route('/mobile-auth-check', methods=['GET'])
def mobile_auth_check():
    """Mobile-specific authentication check with enhanced debugging"""
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
    
    # Check if user is authenticated
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            return jsonify({
                'authenticated': True,
                'user': user.to_dict(),
                'mobile_detected': is_mobile,
                'user_agent': request.headers.get('User-Agent'),
                'session_id': session.sid if hasattr(session, 'sid') else 'No session ID',
                'cookies_present': bool(request.cookies.get('plateiq_session')),
                'session_data': dict(session)
            })
    
    return jsonify({
        'authenticated': False,
        'mobile_detected': is_mobile,
        'user_agent': request.headers.get('User-Agent'),
        'session_id': session.sid if hasattr(session, 'sid') else 'No session ID',
        'cookies_present': bool(request.cookies.get('plateiq_session')),
        'session_data': dict(session),
        'error': 'No valid session found'
    }), 401

@auth_bp.route('/mobile-login', methods=['POST'])
def mobile_login():
    """Mobile-specific login endpoint with enhanced cookie handling"""
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

        current_app.logger.info(f"Mobile login successful for user {username}")

        # Create response with multiple cookie strategies for mobile
        resp = make_response(jsonify({
            'message': 'Mobile login successful',
            'user': user.to_dict(),
            'mobile_optimized': True
        }))

        # Set multiple cookie variants for mobile compatibility
        resp.set_cookie(
            'plateiq_session',
            session.sid if hasattr(session, 'sid') else '',
            secure=True,
            httponly=True,
            samesite='None',
            path='/',
            max_age=86400
        )
        
        # Set a JavaScript-accessible cookie for debugging
        resp.set_cookie(
            'plateiq_mobile_debug',
            'logged_in',
            secure=True,
            httponly=False,
            samesite='None',
            path='/',
            max_age=86400
        )

        return resp
    except Exception as e:
        current_app.logger.error(f"Mobile login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/test-mobile', methods=['GET'])
def test_mobile():
    """Test endpoint to verify mobile detection"""
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad', 'ipod'])
    
    return jsonify({
        'user_agent': request.headers.get('User-Agent'),
        'is_mobile': is_mobile,
        'mobile_keywords_found': [mobile for mobile in ['mobile', 'android', 'iphone', 'ipad', 'ipod'] if mobile in user_agent],
        'timestamp': datetime.utcnow().isoformat()
    })

