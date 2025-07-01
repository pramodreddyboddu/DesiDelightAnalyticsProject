import sys
import os
sys.path.append('.')

from src.models import db, ChefDishMapping, Chef, Item
from src.main import create_app

app = create_app()

with app.app_context():
    print("=== DATABASE STATE CHECK ===")
    
    # Check total counts
    total_items = Item.query.count()
    total_chefs = Chef.query.count()
    total_mappings = ChefDishMapping.query.count()
    
    print(f"Total Items: {total_items}")
    print(f"Total Chefs: {total_chefs}")
    print(f"Total Chef Mappings: {total_mappings}")
    
    # Check for Butter Chicken Masala specifically
    butter_chicken = Item.query.filter(Item.name.ilike('%Butter Chicken%')).first()
    if butter_chicken:
        print(f"\nFound 'Butter Chicken Masala': {butter_chicken.name} (ID: {butter_chicken.id})")
        
        # Check if it's mapped to a chef
        mapping = ChefDishMapping.query.filter_by(item_id=butter_chicken.id).first()
        if mapping:
            chef = Chef.query.get(mapping.chef_id)
            print(f"Mapped to chef: {chef.name if chef else 'Unknown'}")
        else:
            print("NOT MAPPED TO ANY CHEF!")
    else:
        print("\n'Butter Chicken Masala' NOT FOUND in database!")
    
    # Show all chefs
    print(f"\nAll Chefs ({total_chefs}):")
    chefs = Chef.query.all()
    for chef in chefs:
        print(f"  - {chef.name} (ID: {chef.id})")
    
    # Show sample items
    print(f"\nSample Items ({min(5, total_items)}):")
    items = Item.query.limit(5).all()
    for item in items:
        print(f"  - {item.name} (ID: {item.id})")
    
    # Show sample mappings
    print(f"\nSample Mappings ({min(5, total_mappings)}):")
    mappings = ChefDishMapping.query.limit(5).all()
    for mapping in mappings:
        chef = Chef.query.get(mapping.chef_id)
        item = Item.query.get(mapping.item_id)
        print(f"  - {chef.name if chef else 'Unknown'} -> {item.name if item else 'Unknown'}") 