from flask import Blueprint, jsonify
from ..models import db, Item
from ..routes.auth import login_required

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/', methods=['GET'])
@login_required
def get_inventory():
    try:
        # Get all active items
        items = Item.query.filter_by(is_active=True).all()
        
        # Convert to dictionary format
        items_data = [item.to_dict() for item in items]
        
        return jsonify({
            'items': items_data,
            'total': len(items_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 