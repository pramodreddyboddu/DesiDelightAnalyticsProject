#!/usr/bin/env python3
"""
Debug script to check chef mapping consistency and linkage to sales/items
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src import create_app
from src.models import db, ChefDishMapping, Chef, Item, Sale

def debug_mapping_issue():
    app = create_app()
    with app.app_context():
        print("=== DEBUGGING CHEF MAPPING CONSISTENCY ===")
        
        # Total counts
        total_items = Item.query.count()
        total_chefs = Chef.query.count()
        total_mappings = ChefDishMapping.query.count()
        total_sales = Sale.query.count()
        print(f"Total items: {total_items}")
        print(f"Total chefs: {total_chefs}")
        print(f"Total chef mappings: {total_mappings}")
        print(f"Total sales records: {total_sales}")
        
        # Sample mappings
        print("\nSample chef mappings:")
        mappings = ChefDishMapping.query.limit(10).all()
        for m in mappings:
            chef = Chef.query.get(m.chef_id)
            item = Item.query.get(m.item_id)
            print(f"  Mapping ID {m.id}: Chef '{chef.name if chef else 'Unknown'}' -> Item '{item.name if item else 'Unknown'}' (Tenant: {m.tenant_id})")
        
        # Items in sales not mapped to any chef
        print("\nItems in sales with NO chef mapping:")
        sales_item_ids = set(s.item_id for s in Sale.query.all())
        mapped_item_ids = set(m.item_id for m in ChefDishMapping.query.all())
        unmapped_sales_items = sales_item_ids - mapped_item_ids
        if unmapped_sales_items:
            for item_id in list(unmapped_sales_items)[:10]:
                item = Item.query.get(item_id)
                print(f"  Item ID {item_id}: '{item.name if item else 'Unknown'}'")
            print(f"...and {len(unmapped_sales_items)-10} more" if len(unmapped_sales_items) > 10 else "")
        else:
            print("  All sales items are mapped to a chef.")
        
        # Mappings referencing missing items or chefs
        print("\nMappings referencing missing items or chefs:")
        for m in ChefDishMapping.query.limit(20).all():
            chef = Chef.query.get(m.chef_id)
            item = Item.query.get(m.item_id)
            if not chef or not item:
                print(f"  Mapping ID {m.id}: Chef ID {m.chef_id}, Item ID {m.item_id}, Tenant: {m.tenant_id}")
        
        # Check tenant_id consistency
        print("\nChecking tenant_id consistency in mappings:")
        for m in ChefDishMapping.query.limit(20).all():
            item = Item.query.get(m.item_id)
            if item and m.tenant_id != item.tenant_id:
                print(f"  Mapping ID {m.id}: Mapping tenant {m.tenant_id} != Item tenant {item.tenant_id}")
        print("\n=== END OF REPORT ===")

if __name__ == "__main__":
    debug_mapping_issue() 