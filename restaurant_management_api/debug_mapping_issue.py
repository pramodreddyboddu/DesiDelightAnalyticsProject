#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src import create_app
from src.models import db, ChefDishMapping, Chef, Item, Sale

def debug_mapping_issue():
    app = create_app()
    
    with app.app_context():
        print("=== DEBUGGING CHEF MAPPING ISSUE ===")
        
        # Check total items
        total_items = Item.query.count()
        print(f"Total items in database: {total_items}")
        
        # Check total chef mappings
        total_mappings = ChefDishMapping.query.count()
        print(f"Total chef mappings: {total_mappings}")
        
        # Check total sales
        total_sales = Sale.query.count()
        print(f"Total sales records: {total_sales}")
        
        # Get sample items with sales
        items_with_sales = db.session.query(Item.id, Item.name, Item.tenant_id).join(Sale, Item.id == Sale.item_id).distinct().limit(10).all()
        print(f"\nSample items with sales:")
        for item_id, item_name, tenant_id in items_with_sales:
            print(f"  Item ID: {item_id}, Name: '{item_name}', Tenant: {tenant_id}")
        
        # Check which items have mappings
        mapped_items = db.session.query(ChefDishMapping.item_id).distinct().all()
        mapped_item_ids = set(item_id for (item_id,) in mapped_items)
        print(f"\nItems with chef mappings: {len(mapped_item_ids)}")
        
        # Check which items with sales don't have mappings
        items_with_sales_no_mapping = db.session.query(Item.id, Item.name, Item.tenant_id).join(Sale, Item.id == Sale.item_id).filter(~Item.id.in_(mapped_item_ids)).distinct().limit(10).all()
        print(f"\nSample items with sales but NO chef mappings:")
        for item_id, item_name, tenant_id in items_with_sales_no_mapping:
            print(f"  Item ID: {item_id}, Name: '{item_name}', Tenant: {tenant_id}")
        
        # Check chef mappings by tenant
        print(f"\nChef mappings by tenant:")
        tenant_mappings = db.session.query(ChefDishMapping.tenant_id, db.func.count(ChefDishMapping.id)).group_by(ChefDishMapping.tenant_id).all()
        for tenant_id, count in tenant_mappings:
            print(f"  Tenant {tenant_id}: {count} mappings")
        
        # Check items by tenant
        print(f"\nItems by tenant:")
        tenant_items = db.session.query(Item.tenant_id, db.func.count(Item.id)).group_by(Item.tenant_id).all()
        for tenant_id, count in tenant_items:
            print(f"  Tenant {tenant_id}: {count} items")
        
        # Check if there are any items with exact names that should match
        print(f"\nChecking for potential name mismatches...")
        sample_unmapped = items_with_sales_no_mapping[:5]
        for item_id, item_name, tenant_id in sample_unmapped:
            # Look for similar names in chef mappings
            similar_mappings = ChefDishMapping.query.join(Item, ChefDishMapping.item_id == Item.id).filter(
                Item.name.like(f"%{item_name}%") | Item.name.like(f"%{item_name.strip()}%")
            ).limit(3).all()
            
            if similar_mappings:
                print(f"  Item '{item_name}' might have similar mappings:")
                for mapping in similar_mappings:
                    item = Item.query.get(mapping.item_id)
                    chef = Chef.query.get(mapping.chef_id)
                    print(f"    Similar: '{item.name}' -> '{chef.name}'")
            else:
                print(f"  Item '{item_name}' - no similar mappings found")

if __name__ == "__main__":
    debug_mapping_issue() 