from flask import Blueprint, jsonify, current_app, request
from sqlalchemy import func
from ..models import db, Item
from ..routes.auth import login_required

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('', methods=['GET', 'OPTIONS'])
@inventory_bp.route('/', methods=['GET', 'OPTIONS'])
@login_required
def get_inventory():
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = current_app.make_response('')
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cookie'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '600'
        return response, 200

    try:
        # Use query optimization for large datasets
        items_query = Item.query.filter_by(is_active=True)\
            .with_entities(
                Item.id,
                Item.name,
                Item.category,
                Item.price,
                Item.quantity,
                Item.sku,
                Item.product_code,
                Item.updated_at
            )\
            .order_by(Item.category, Item.name)
        
        # Execute query efficiently
        items = items_query.all()
        
        # Convert to dictionary format with minimal processing
        items_data = [{
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'price': float(item.price) if item.price else 0.0,
            'quantity': item.quantity,
            'sku': item.sku,
            'product_code': item.product_code,
            'last_updated': item.updated_at.isoformat() if item.updated_at else None
        } for item in items]
        
        response = jsonify({
            'items': items_data,
            'total': len(items_data)
        })
        
        # Add CORS headers to response
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response, 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching inventory: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch inventory data',
            'details': str(e)
        }), 500 