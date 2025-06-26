from flask import Blueprint, request, jsonify, current_app
from src.services.clover_service import CloverService, CloverConfig
from src.utils.auth import login_required, admin_required
from src.models import db
from src.models.sale import Sale
from src.models.item import Item
import logging
from datetime import datetime, timedelta
import os

clover_bp = Blueprint('clover', __name__, url_prefix='/clover')
logger = logging.getLogger(__name__)

def get_clover_service():
    """Get Clover service instance"""
    config = CloverConfig(
        merchant_id=os.getenv('CLOVER_MERCHANT_ID'),
        access_token=os.getenv('CLOVER_ACCESS_TOKEN')
    )
    return CloverService(config)

@clover_bp.route('/status', methods=['GET'])
@login_required
def get_clover_status():
    """Check Clover integration status"""
    try:
        clover_service = get_clover_service()
        merchant_info = clover_service.get_merchant_info()
        
        return jsonify({
            'merchant': merchant_info,
            'last_sync': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Clover status check failed: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@clover_bp.route('/sync/sales', methods=['POST'])
@admin_required
def sync_sales():
    """Sync sales data from Clover to local database"""
    try:
        # Get date range from request
        data = request.get_json() or {}
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        clover_service = get_clover_service()
        result = clover_service.sync_sales_data(start_date, end_date)
        
        return jsonify(result), 200 if result['status'] == 'success' else 500
        
    except Exception as e:
        logger.error(f"Sales sync failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/sync/inventory', methods=['POST'])
@admin_required
def sync_inventory():
    """Sync inventory data from Clover to local database"""
    try:
        clover_service = get_clover_service()
        result = clover_service.sync_inventory_data()
        
        return jsonify(result), 200 if result['status'] == 'success' else 500
        
    except Exception as e:
        logger.error(f"Inventory sync failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/realtime', methods=['GET'])
@login_required
def get_real_time_data():
    """Get real-time data from Clover"""
    try:
        clover_service = get_clover_service()
        data = clover_service.get_real_time_data()
        
        return jsonify(data), 200
        
    except Exception as e:
        logger.error(f"Real-time data fetch failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/inventory', methods=['GET'])
@login_required
def get_inventory():
    """Get current inventory from Clover"""
    try:
        clover_service = get_clover_service()
        inventory = clover_service.get_inventory_levels()
        
        return jsonify({
            'inventory': inventory,
            'count': len(inventory)
        }), 200
        
    except Exception as e:
        logger.error(f"Inventory fetch failed: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@clover_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Get orders from Clover"""
    try:
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        clover_service = get_clover_service()
        orders = clover_service.get_orders(start_date, end_date, limit)
        
        return jsonify({
            'orders': orders,
            'count': len(orders)
        }), 200
        
    except Exception as e:
        logger.error(f"Orders fetch failed: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@clover_bp.route('/orders/<order_id>', methods=['GET'])
@login_required
def get_order_details(order_id):
    """Get detailed order information"""
    try:
        clover_service = get_clover_service()
        order_details = clover_service.get_order_details(order_id)
        
        return jsonify({
            'status': 'success',
            'data': order_details
        }), 200
        
    except Exception as e:
        logger.error(f"Order details fetch failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/employees', methods=['GET'])
@login_required
def get_employees():
    """Get employees from Clover"""
    try:
        clover_service = get_clover_service()
        employees = clover_service.get_employees()
        
        return jsonify({
            'employees': employees,
            'count': len(employees)
        }), 200
        
    except Exception as e:
        logger.error(f"Employees fetch failed: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@clover_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    """Get customers from Clover"""
    try:
        clover_service = get_clover_service()
        customers = clover_service.get_customers()
        
        return jsonify({
            'customers': customers,
            'count': len(customers)
        }), 200
        
    except Exception as e:
        logger.error(f"Customers fetch failed: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@clover_bp.route('/items', methods=['GET'])
@login_required
def get_items():
    """Get items from Clover"""
    try:
        category_id = request.args.get('category_id')
        clover_service = get_clover_service()
        items = clover_service.get_items(category_id)
        
        return jsonify({
            'status': 'success',
            'data': items,
            'count': len(items)
        }), 200
        
    except Exception as e:
        logger.error(f"Items fetch failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Get categories from Clover"""
    try:
        clover_service = get_clover_service()
        categories = clover_service.get_categories()
        
        return jsonify({
            'status': 'success',
            'data': categories,
            'count': len(categories)
        }), 200
        
    except Exception as e:
        logger.error(f"Categories fetch failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/sync/all', methods=['POST'])
@admin_required
def sync_all():
    """Sync all data from Clover to local database"""
    try:
        clover_service = get_clover_service()
        
        # Sync sales data
        sales_result = clover_service.sync_sales_data()
        
        # Sync inventory data
        inventory_result = clover_service.sync_inventory_data()
        
        return jsonify({
            'status': 'success',
            'sales_sync': sales_result,
            'inventory_sync': inventory_result,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/debug/items', methods=['GET'])
@admin_required
def debug_items():
    """Get raw item data from Clover for debugging"""
    try:
        clover_service = get_clover_service()
        items = clover_service.get_items()
        
        # Return first 3 items with full details for debugging
        debug_items = items[:3] if items else []
        
        return jsonify({
            'status': 'success',
            'debug_items': debug_items,
            'total_items': len(items) if items else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Debug items fetch failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@clover_bp.route('/clear-cache', methods=['POST'])
@admin_required
def clear_cache():
    """Clear Clover cache to force fresh data fetch"""
    try:
        from src.services.dashboard_service import DashboardService
        dashboard_service = DashboardService()
        dashboard_service.clear_clover_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Cache cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 