from flask import Blueprint, jsonify, current_app, request
from ..models import db, Sale, Item, Expense, ChefDishMapping
from ..utils.auth import tenant_admin_required
from sqlalchemy import func
import pytz
from datetime import datetime

tenant_data_bp = Blueprint('tenant_data', __name__)

@tenant_data_bp.route('/stats', methods=['GET'])
@tenant_admin_required
def get_tenant_data_stats():
    """Get statistics about the data for the logged-in tenant."""
    tenant_id = request.tenant_id
    stats = {
        'sales': {'count': 0, 'last_updated': None},
        'inventory': {'count': 0, 'last_updated': None},
        'expenses': {'count': 0, 'last_updated': None},
        'chef_mapping': {'count': 0, 'last_updated': None},
    }

    def format_timestamp(ts):
        if ts is None: return None
        if isinstance(ts, str): return ts
        try:
            # Assuming incoming timestamps are naive UTC, localize them
            cst = pytz.timezone('America/Chicago')
            utc_ts = pytz.utc.localize(ts) if ts.tzinfo is None else ts
            return utc_ts.astimezone(cst).strftime('%Y-%m-%dT%H:%M:%S')
        except Exception as e:
            current_app.logger.error(f"Error formatting timestamp {ts}: {str(e)}")
            return None # Return None on failure

    try:
        # Sales stats
        try:
            stats['sales']['count'] = db.session.query(func.count(Sale.id)).filter(Sale.tenant_id == tenant_id).scalar() or 0
            last_sales_update = db.session.query(func.max(Sale.line_item_date)).filter(Sale.tenant_id == tenant_id).scalar()
            stats['sales']['last_updated'] = format_timestamp(last_sales_update)
        except Exception as e:
            current_app.logger.error(f"Error getting sales stats for tenant {tenant_id}: {e}")

        # Inventory stats
        try:
            stats['inventory']['count'] = db.session.query(func.count(Item.id)).filter(Item.tenant_id == tenant_id, Item.is_active == True).scalar() or 0
            last_inventory_update = db.session.query(func.max(Item.updated_at)).filter(Item.tenant_id == tenant_id).scalar()
            stats['inventory']['last_updated'] = format_timestamp(last_inventory_update)
        except Exception as e:
            current_app.logger.error(f"Error getting inventory stats for tenant {tenant_id}: {e}")

        # Expenses stats
        try:
            stats['expenses']['count'] = db.session.query(func.count(Expense.id)).filter(Expense.tenant_id == tenant_id).scalar() or 0
            last_expenses_update = db.session.query(func.max(Expense.date)).filter(Expense.tenant_id == tenant_id).scalar()
            stats['expenses']['last_updated'] = format_timestamp(last_expenses_update)
        except Exception as e:
            current_app.logger.error(f"Error getting expenses stats for tenant {tenant_id}: {e}")

        # Chef Mapping stats
        try:
            stats['chef_mapping']['count'] = db.session.query(func.count(ChefDishMapping.id)).filter(ChefDishMapping.tenant_id == tenant_id).scalar() or 0
            last_chef_mapping_update = db.session.query(func.max(ChefDishMapping.created_at)).filter(ChefDishMapping.tenant_id == tenant_id).scalar()
            stats['chef_mapping']['last_updated'] = format_timestamp(last_chef_mapping_update)
        except Exception as e:
            current_app.logger.error(f"Error getting chef mapping stats for tenant {tenant_id}: {e}")

        return jsonify(stats)

    except Exception as e:
        current_app.logger.error(f"A general error occurred in tenant data stats for tenant {tenant_id}: {e}")
        # Fallback to returning the partially filled stats object with an error status
        return jsonify({'error': f'An error occurred: {e}', 'stats': stats}), 500 