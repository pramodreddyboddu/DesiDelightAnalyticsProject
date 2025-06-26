from flask import Blueprint, jsonify, current_app, request
from sqlalchemy import func
from ..models import db, Item
from ..routes.auth import login_required
from ..services.dashboard_service import DashboardService

inventory_bp = Blueprint('inventory', __name__)
dashboard_service = DashboardService()

@inventory_bp.route('', methods=['GET'])
@inventory_bp.route('/', methods=['GET'])
@login_required
def get_inventory():
    try:
        # Use dashboard service to get inventory data from configured source
        inventory_data = dashboard_service.get_inventory_data()
        
        return jsonify(inventory_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching inventory: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch inventory data',
            'details': str(e)
        }), 500

@inventory_bp.route('/categories', methods=['GET'])
@login_required
def get_inventory_categories():
    try:
        # Use Clover if configured, else local
        data_source = dashboard_service.get_data_source('inventory')
        if data_source == 'clover':
            categories = dashboard_service.clover_service.get_categories()
            category_names = sorted({cat.get('name', 'Uncategorized') for cat in categories if cat.get('name')})
        else:
            # Local DB fallback
            category_names = [row[0] for row in db.session.query(Item.category).distinct().all() if row[0]]
        return jsonify({'categories': category_names}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 