from flask import Blueprint, jsonify, current_app, request
from sqlalchemy import func
from ..models import db, Item
from ..routes.auth import login_required

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('', methods=['GET'])
@inventory_bp.route('/', methods=['GET'])
@login_required
def get_inventory():
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
        
        return jsonify({
            'items': items_data,
            'total': len(items_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching inventory: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch inventory data',
            'details': str(e)
        }), 500 