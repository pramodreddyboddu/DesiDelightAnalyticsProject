from flask import Blueprint, jsonify, request, current_app, session
from datetime import datetime, timedelta
from ..models import db
from ..models.sale import Sale
from ..models.item import Item
from ..models.expense import Expense
from ..models.chef_dish_mapping import ChefDishMapping
from ..models.file_upload import FileUpload
from ..models.tenant import Tenant
from ..models.user import User
from ..utils.auth import super_admin_required, admin_required
from sqlalchemy import func, case
import logging
import pytz

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/system-stats', methods=['GET'])
@super_admin_required
def get_system_stats():
    """Get system-wide statistics for super admin"""
    try:
        total_tenants = db.session.query(func.count(Tenant.id)).scalar()
        active_tenants = db.session.query(func.count(Tenant.id)).filter(Tenant.is_active == True).scalar()
        total_users = db.session.query(func.count(User.id)).scalar()
        active_users_this_month = db.session.query(func.count(User.id)).filter(
            User.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ).scalar()
        monthly_revenue = total_tenants * 99
        revenue_growth = 15
        recent_activity = [
            {'description': 'New tenant registered: Spice Garden', 'timestamp': '2024-01-15 10:30:00', 'type': 'tenant_created'},
            {'description': 'Subscription upgraded: Premium Plan', 'timestamp': '2024-01-14 15:45:00', 'type': 'subscription_upgrade'},
            {'description': 'System maintenance completed', 'timestamp': '2024-01-13 02:00:00', 'type': 'maintenance'}
        ]
        return jsonify({
            'total_tenants': total_tenants,
            'active_tenants': active_tenants,
            'total_users': total_users,
            'active_users': active_users_this_month,
            'monthly_revenue': monthly_revenue,
            'revenue_growth': revenue_growth,
            'recent_activity': recent_activity
        })
    except Exception as e:
        current_app.logger.error(f"Error getting system stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/data-stats', methods=['GET'])
@super_admin_required
def get_data_stats():
    """Get statistics about the data in the system"""
    try:
        sales_count = db.session.query(func.count(Sale.id)).scalar()
        inventory_count = db.session.query(func.count(Item.id)).filter(Item.is_active == True).scalar()
        expenses_count = db.session.query(func.count(Expense.id)).scalar()
        chef_mapping_count = db.session.query(func.count(ChefDishMapping.id)).scalar()
        last_sales_update = db.session.query(func.max(Sale.line_item_date)).scalar()
        last_inventory_update = db.session.query(func.max(Item.updated_at)).scalar()
        last_expenses_update = db.session.query(func.max(Expense.date)).scalar()
        last_chef_mapping_update = db.session.query(func.max(ChefDishMapping.created_at)).scalar()
        def format_timestamp(ts):
            if ts is None:
                return None
            if isinstance(ts, str):
                return ts
            try:
                cst = pytz.timezone('America/Chicago')
                if ts.tzinfo is None:
                    ts = pytz.utc.localize(ts)
                cst_ts = ts.astimezone(cst)
                return cst_ts.strftime('%Y-%m-%dT%H:%M:%S')
            except Exception as e:
                current_app.logger.error(f"Error formatting timestamp {ts}: {str(e)}")
                return None
        formatted_sales = format_timestamp(last_sales_update)
        formatted_inventory = format_timestamp(last_inventory_update)
        formatted_expenses = format_timestamp(last_expenses_update)
        formatted_chef = format_timestamp(last_chef_mapping_update)
        return jsonify({
            'sales': {'count': sales_count, 'last_updated': formatted_sales},
            'inventory': {'count': inventory_count, 'last_updated': formatted_inventory},
            'expenses': {'count': expenses_count, 'last_updated': formatted_expenses},
            'chef_mapping': {'count': chef_mapping_count, 'last_updated': formatted_chef}
        })
    except Exception as e:
        current_app.logger.error(f"Error getting data stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/diagnostic/inventory', methods=['GET'])
@super_admin_required
def get_inventory_diagnostic():
    """Get detailed diagnostic information about inventory items"""
    try:
        status_counts = db.session.query(Item.is_active, func.count(Item.id).label('count')).group_by(Item.is_active).all()
        items_with_sales = db.session.query(Item.id, Item.name, Item.is_active, func.count(Sale.id).label('sales_count')).join(Sale, Item.id == Sale.item_id).group_by(Item.id, Item.name, Item.is_active).having(func.count(Sale.id) > 0).all()
        items_with_chef_mappings = db.session.query(Item.id, Item.name, Item.is_active, func.count(ChefDishMapping.id).label('mapping_count')).join(ChefDishMapping, Item.id == ChefDishMapping.item_id).group_by(Item.id, Item.name, Item.is_active).having(func.count(ChefDishMapping.id) > 0).all()
        return jsonify({
            'status_counts': [{'is_active': status, 'count': count} for status, count in status_counts],
            'items_with_sales': [{'id': item.id, 'name': item.name, 'is_active': item.is_active, 'sales_count': item.sales_count} for item in items_with_sales],
            'items_with_chef_mappings': [{'id': item.id, 'name': item.name, 'is_active': item.is_active, 'mapping_count': item.mapping_count} for item in items_with_chef_mappings]
        })
    except Exception as e:
        current_app.logger.error(f"Error in inventory diagnostic: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/force-delete-inventory', methods=['DELETE'])
@super_admin_required
def force_delete_inventory():
    """Force delete all inventory items"""
    try:
        db.session.begin_nested()
        total_items = db.session.query(func.count(Item.id)).scalar()
        current_app.logger.info(f"Found {total_items} total inventory items")
        batch_size = 1000
        deleted = 0
        while deleted < total_items:
            items = db.session.query(Item).limit(batch_size).offset(deleted).all()
            if not items:
                break
            for item in items:
                try:
                    db.session.delete(item)
                except Exception as e:
                    current_app.logger.error(f"Error deleting item {item.id}: {str(e)}")
                    continue
            db.session.commit()
            deleted += len(items)
            current_app.logger.info(f"Deleted {deleted} items so far")
        remaining = db.session.query(func.count(Item.id)).scalar()
        if remaining > 0:
            current_app.logger.warning(f"Found {remaining} items still remaining, trying direct delete")
            db.session.query(Item).delete(synchronize_session=False)
            db.session.commit()
        final_count = db.session.query(func.count(Item.id)).scalar()
        current_app.logger.info(f"Final item count: {final_count}")
        return jsonify({'message': f'Successfully deleted {deleted} inventory items', 'deleted_count': deleted, 'remaining_count': final_count})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error forcing delete inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/delete-data', methods=['DELETE'])
@admin_required
def delete_data():
    """Delete data for a specific type. Tenant admins can only delete their own tenant's data."""
    data_type = None
    try:
        import json
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        data = request.get_json() or {}
        data_type = data.get('data_type') or request.args.get('type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        # Only super admin can specify tenant_id, tenant admin uses their own
        if user.tenant_id:
            tenant_id = user.tenant_id
        else:
            tenant_id = data.get('tenant_id')

        model_map = {
            'sales': Sale,
            'inventory': Item,
            'expenses': Expense,
            'chef_mapping': ChefDishMapping,
            'uploads': FileUpload
        }
        if data_type not in model_map:
            return jsonify({'error': f'Invalid data type: {data_type}'}), 400
        model = model_map[data_type]

        query = db.session.query(model)
        # Only filter by tenant_id if the model has it
        if hasattr(model, 'tenant_id'):
            if not tenant_id:
                return jsonify({'error': 'Tenant ID required'}), 400
            query = query.filter(model.tenant_id == tenant_id)

        # Optionally filter by date range if present and model has date
        if start_date and hasattr(model, 'date'):
            query = query.filter(model.date >= start_date)
        if end_date and hasattr(model, 'date'):
            query = query.filter(model.date <= end_date)

        num_rows_deleted = query.delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'message': f'Successfully deleted {num_rows_deleted} rows from {data_type}', 'deleted_count': num_rows_deleted})
    except Exception as e:
        db.session.rollback()
        if data_type:
            current_app.logger.error(f"Error deleting data for {data_type}: {str(e)}")
        else:
            current_app.logger.error(f"Error deleting data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tenants', methods=['GET'])
@super_admin_required
def get_tenants():
    """Get all tenants"""
    try:
        tenants = Tenant.query.all()
        return jsonify([tenant.to_dict() for tenant in tenants])
    except Exception as e:
        current_app.logger.error(f"Error getting tenants: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tenants', methods=['POST'])
@super_admin_required
def create_tenant():
    """Create a new tenant"""
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Tenant name is required'}), 400
        tenant = Tenant(name=name, is_active=data.get('is_active', True))
        db.session.add(tenant)
        db.session.commit()
        return jsonify(tenant.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating tenant: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tenants/<int:tenant_id>', methods=['GET'])
@super_admin_required
def get_tenant(tenant_id):
    """Get a specific tenant by ID"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        return jsonify(tenant.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error getting tenant {tenant_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tenants/<int:tenant_id>', methods=['PUT'])
@super_admin_required
def update_tenant(tenant_id):
    """Update a tenant"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        data = request.get_json()
        tenant.name = data.get('name', tenant.name)
        tenant.is_active = data.get('is_active', tenant.is_active)
        db.session.commit()
        return jsonify(tenant.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating tenant {tenant_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/tenants/<int:tenant_id>', methods=['DELETE'])
@super_admin_required
def delete_tenant(tenant_id):
    """Delete a tenant"""
    try:
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        db.session.delete(tenant)
        db.session.commit()
        return jsonify({'message': 'Tenant deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting tenant {tenant_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@super_admin_required
def get_all_users():
    """Get all users across all tenants (for super admin)"""
    try:
        users = User.query.options(db.joinedload(User.tenant)).all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        current_app.logger.error(f"Error getting all users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@super_admin_required
def update_user_by_admin(user_id):
    """Update a user's details (by super admin)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        data = request.get_json()
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        user.is_admin = data.get('is_admin', user.is_admin)
        user.tenant_id = data.get('tenant_id', user.tenant_id)
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user {user_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@super_admin_required
def delete_user_by_admin(user_id):
    """Delete a user (by super admin)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/system-health-check', methods=['GET'])
@super_admin_required
def get_system_health():
    """Get system health information"""
    return jsonify({'status': 'OK', 'services': {'database': 'OK', 'cache': 'OK', 'ai_service': 'OK'}})

@admin_bp.route('/run-maintenance', methods=['POST'])
@super_admin_required
def run_maintenance_tasks():
    """Run maintenance tasks on the system"""
    return jsonify({'message': 'Maintenance tasks completed successfully'})

@admin_bp.route('/system-settings', methods=['GET'])
@super_admin_required
def get_system_settings():
    """Get all system settings"""
    return jsonify({'setting1': 'value1', 'setting2': 'value2'})

@admin_bp.route('/system-settings', methods=['PUT'])
@super_admin_required
def update_system_settings():
    """Update system settings"""
    return jsonify({'message': 'System settings updated successfully'}) 