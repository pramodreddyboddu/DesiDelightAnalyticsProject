from flask import Blueprint, request, jsonify
from src.models import db
from src.models.tenant import Tenant
from src.models.user import User
from src.utils.auth import login_required, super_admin_required
from datetime import datetime, timedelta
import logging

tenant_bp = Blueprint('tenant', __name__)
logger = logging.getLogger(__name__)

@tenant_bp.route('/tenants', methods=['GET'])
@super_admin_required
def get_tenants():
    """Get all tenants (super admin only)"""
    try:
        tenants = Tenant.query.all()
        return jsonify({
            'status': 'success',
            'data': [tenant.to_dict() for tenant in tenants]
        }), 200
    except Exception as e:
        logger.error(f"Error getting tenants: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get tenants'
        }), 500

@tenant_bp.route('/tenants/<tenant_id>', methods=['GET'])
@login_required
def get_tenant(tenant_id):
    """Get specific tenant details"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({
                'status': 'error',
                'message': 'Tenant not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': tenant.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting tenant {tenant_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get tenant'
        }), 500

@tenant_bp.route('/tenants', methods=['POST'])
@super_admin_required
def create_tenant():
    """Create a new tenant (super admin only)"""
    logger.info("Received request to create a new tenant.")
    logger.debug(f"Request Headers: {request.headers}")
    logger.debug(f"Request Data: {request.data}")
    try:
        data = request.get_json()
        if not data:
            logger.warning("Create tenant request failed: No JSON data received.")
            return jsonify({'status': 'error', 'message': 'Request must contain valid JSON.'}), 400
        
        logger.info(f"Tenant creation data received: {data}")
        
        # Validate required fields
        required_fields = ['name', 'business_type', 'contact_email']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            logger.warning(f"Tenant creation failed. Missing fields: {', '.join(missing_fields)}")
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Check if email already exists
        existing_tenant = Tenant.query.filter_by(contact_email=data['contact_email']).first()
        if existing_tenant:
            return jsonify({
                'status': 'error',
                'message': 'Email already registered'
            }), 400
        
        # Create tenant
        tenant = Tenant(
            name=data['name'],
            business_type=data['business_type'],
            contact_email=data['contact_email'],
            contact_phone=data.get('contact_phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            country=data.get('country', 'US'),
            postal_code=data.get('postal_code'),
            subscription_plan=data.get('subscription_plan', 'free'),
            trial_ends_at=datetime.utcnow() + timedelta(days=30),  # 30-day trial
            is_trial=True
        )
        
        db.session.add(tenant)
        db.session.commit()
        
        # Create default admin user for tenant
        admin_user = User(
            username=f"admin_{tenant.id[:8]}",
            email=data['contact_email'],
            role='admin',
            is_admin=True,
            tenant_id=tenant.id
        )
        admin_user.set_password('changeme123')  # Default password
        db.session.add(admin_user)
        db.session.commit()
        
        logger.info(f"Created new tenant: {tenant.name} ({tenant.id})")
        
        return jsonify({
            'status': 'success',
            'message': 'Tenant created successfully',
            'data': {
                'tenant': tenant.to_dict(),
                'admin_credentials': {
                    'username': admin_user.username,
                    'password': 'changeme123'
                }
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating tenant: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Failed to create tenant'
        }), 500

@tenant_bp.route('/tenants/<tenant_id>', methods=['PUT'])
@super_admin_required
def update_tenant(tenant_id):
    """Update tenant details (super admin only)"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({
                'status': 'error',
                'message': 'Tenant not found'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = [
            'name', 'business_type', 'contact_phone', 'address', 'city', 
            'state', 'country', 'postal_code', 'subscription_plan', 
            'subscription_status', 'billing_cycle', 'next_billing_date',
            'timezone', 'currency', 'language', 'logo_url', 'primary_color',
            'custom_domain', 'is_active', 'max_users'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(tenant, field, data[field])
        
        tenant.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Tenant updated successfully',
            'data': tenant.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating tenant {tenant_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Failed to update tenant'
        }), 500

@tenant_bp.route('/tenants/<tenant_id>/users', methods=['GET'])
@login_required
def get_tenant_users(tenant_id):
    """Get users for a specific tenant"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({
                'status': 'error',
                'message': 'Tenant not found'
            }), 404
        
        users = User.query.filter_by(tenant_id=tenant_id).all()
        
        return jsonify({
            'status': 'success',
            'data': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users for tenant {tenant_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get tenant users'
        }), 500

@tenant_bp.route('/tenants/<tenant_id>/stats', methods=['GET'])
@login_required
def get_tenant_stats(tenant_id):
    """Get tenant usage statistics"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({
                'status': 'error',
                'message': 'Tenant not found'
            }), 404
        
        # Get plan limits
        plan_limits = tenant.get_plan_limits()
        
        # Get current usage
        current_users = len(tenant.users)
        
        stats = {
            'tenant': tenant.to_dict(),
            'usage': {
                'current_users': current_users,
                'max_users': plan_limits['max_users'],
                'api_calls_this_month': tenant.api_calls_this_month,
                'max_api_calls_per_month': plan_limits['max_api_calls_per_month'],
                'storage_used_mb': tenant.storage_used_mb,
                'max_storage_mb': plan_limits['max_storage_mb']
            },
            'plan_limits': plan_limits,
            'can_add_users': tenant.can_add_users,
            'is_trial_expired': tenant.is_trial_expired
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats for tenant {tenant_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get tenant stats'
        }), 500 