import sys
import os
sys.path.append('restaurant_management_api')

from restaurant_management_api.src.models import db, ChefDishMapping, Chef, Item, Sale
from restaurant_management_api.src.main import create_app
from restaurant_management_api.src.services.clover_service import CloverService
from restaurant_management_api.src.config import get_clover_config

app = create_app()

with app.app_context():
    print("=== FIXING CLOVER ITEM MAPPING ===")
    
    # Get Clover configuration
    config = get_clover_config()
    if not config:
        print("No Clover configuration found")
        exit(1)
    
    clover_service = CloverService(config)
    
    try:
        # Get Clover items
        print("Fetching items from Clover...")
        clover_items = clover_service.get_items()
        print(f"Found {len(clover_items)} items in Clover")
        
        # Create mapping from Clover item name to Clover item ID
        clover_name_to_id = {}
        for clover_item in clover_items:
            name = clover_item.get('name', '').strip()
            clover_id = clover_item.get('id')
            if name and clover_id:
                clover_name_to_id[name] = clover_id
        
        print(f"Created mapping for {len(clover_name_to_id)} Clover items")
        
        # Get all local items
        local_items = Item.query.all()
        print(f"Found {len(local_items)} local items")
        
        # Update local items with correct clover_id
        updated_count = 0
        for local_item in local_items:
            local_name = local_item.name.strip()
            if local_name in clover_name_to_id:
                correct_clover_id = clover_name_to_id[local_name]
                if local_item.clover_id != correct_clover_id:
                    print(f"Updating item '{local_name}': {local_item.clover_id} -> {correct_clover_id}")
                    local_item.clover_id = correct_clover_id
                    updated_count += 1
                else:
                    print(f"Item '{local_name}' already has correct clover_id: {correct_clover_id}")
            else:
                print(f"Item '{local_name}' not found in Clover")
        
        if updated_count > 0:
            db.session.commit()
            print(f"Updated {updated_count} items with correct clover_id")
        else:
            print("No items needed updating")
        
        # Now check chef mappings
        chef_mappings = ChefDishMapping.query.all()
        print(f"\nFound {len(chef_mappings)} chef mappings")
        
        # Check which mapped items now have correct clover_id
        mapped_items_with_clover = 0
        for mapping in chef_mappings:
            item = Item.query.get(mapping.item_id)
            if item and item.clover_id and item.clover_id in clover_name_to_id.values():
                mapped_items_with_clover += 1
        
        print(f"Chef-mapped items with correct clover_id: {mapped_items_with_clover}")
        
        # Test the mapping
        item_id_map = {item.clover_id: item.id for item in local_items if item.clover_id}
        print(f"Items with clover_id in mapping: {len(item_id_map)}")
        
        # Check how many Clover items can be mapped
        mappable_count = 0
        for clover_id in clover_name_to_id.values():
            if clover_id in item_id_map:
                mappable_count += 1
        
        print(f"Clover items that can be mapped to local items: {mappable_count}")
        
        # Check sales data
        total_sales = Sale.query.count()
        print(f"\nTotal sales records: {total_sales}")
        
        # Check which sales items have mappings
        sales_items = set(row[0] for row in db.session.query(Sale.item_id).all())
        mapped_item_ids = set(mapping.item_id for mapping in chef_mappings)
        unmapped_sales_items = sales_items - mapped_item_ids
        print(f"Sales items without chef mappings: {len(unmapped_sales_items)}")
        
        print("\n=== MAPPING FIX COMPLETE ===")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc() 