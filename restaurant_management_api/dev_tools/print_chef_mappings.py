import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import db, ChefDishMapping, Chef, Item
from src.main import create_app

app = create_app()

with app.app_context():
    chef_name = input('Enter chef name to print mappings for: ').strip()
    chefs = Chef.query.filter(db.func.lower(Chef.name) == chef_name.lower()).all()
    if not chefs:
        print(f"No chef found with name '{chef_name}'")
        sys.exit(0)
    for chef in chefs:
        print(f"\nMappings for Chef: {chef.name} (ID: {chef.id})")
        mappings = ChefDishMapping.query.filter_by(chef_id=chef.id).all()
        if not mappings:
            print("  No mappings found.")
            continue
        for mapping in mappings:
            item = Item.query.get(mapping.item_id)
            print(f"  Item: {item.name if item else 'Unknown'} | Clover ID: {item.clover_id if item else 'Unknown'} | Mapping Active: {getattr(mapping, 'is_active', 'N/A')}") 