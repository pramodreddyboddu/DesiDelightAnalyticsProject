#!/usr/bin/env python3
"""
Debug script: Check for Clover sales item IDs missing from local item table, and for items missing chef mappings.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import app, db
from src.services.clover_service import CloverService, CloverConfig
from src.models.item import Item
from src.models.chef_dish_mapping import ChefDishMapping
from src.models.chef import Chef


def main():
    with app.app_context():
        print("=== CLOVER ITEM MAPPING DEBUG ===")
        clover_config = CloverConfig(
            merchant_id=os.getenv('CLOVER_MERCHANT_ID', ''),
            access_token=os.getenv('CLOVER_ACCESS_TOKEN', '')
        )
        clover_service = CloverService(clover_config)
        # Get recent orders from Clover
        print("Fetching recent orders from Clover API...")
        orders = clover_service.get_orders()
        clover_item_ids = set()
        
        if orders:
            print(f"Found {len(orders)} orders from Clover")
            # Extract unique Clover item IDs from orders
            for order in orders:
                line_items = order.get('lineItems', {}).get('elements', [])
                for line_item in line_items:
                    item = line_item.get('item', {})
                    clover_item_id = item.get('id')
                    if clover_item_id:
                        clover_item_ids.add(clover_item_id)
        else:
            print("No orders found from Clover API")
            return
        
        print(f"Found {len(clover_item_ids)} unique Clover item IDs in recent sales")
        
        # Check which Clover item IDs exist in local item table
        local_items = Item.query.all()
        local_clover_ids = {item.clover_id for item in local_items if item.clover_id}
        
        print(f"Local database has {len(local_items)} items, {len(local_clover_ids)} with clover_id")
        
        # Find missing items
        missing_clover_ids = clover_item_ids - local_clover_ids
        found_clover_ids = clover_item_ids & local_clover_ids
        
        print(f"\n📊 MAPPING ANALYSIS:")
        print(f"   Clover sales items: {len(clover_item_ids)}")
        print(f"   Found in local DB: {len(found_clover_ids)}")
        print(f"   Missing from local DB: {len(missing_clover_ids)}")
        
        if missing_clover_ids:
            print(f"\n❌ MISSING ITEMS (not in local item table):")
            for clover_id in list(missing_clover_ids)[:10]:  # Show first 10
                print(f"   - {clover_id}")
            if len(missing_clover_ids) > 10:
                print(f"   ... and {len(missing_clover_ids) - 10} more")
        
        # Check chef mappings for found items
        if found_clover_ids:
            print(f"\n🔍 CHECKING CHEF MAPPINGS FOR FOUND ITEMS:")
            mapped_count = 0
            unmapped_count = 0
            
            for clover_id in found_clover_ids:
                local_item = Item.query.filter_by(clover_id=clover_id).first()
                if local_item:
                    mapping = ChefDishMapping.query.filter_by(item_id=local_item.id).first()
                    if mapping:
                        chef = Chef.query.get(mapping.chef_id)
                        chef_name = chef.name if chef else "Unknown"
                        mapped_count += 1
                        print(f"   ✅ {clover_id} -> {local_item.name} -> {chef_name}")
                    else:
                        unmapped_count += 1
                        print(f"   ❌ {clover_id} -> {local_item.name} -> NO CHEF MAPPING")
            
            print(f"\n📈 CHEF MAPPING SUMMARY:")
            print(f"   Items with chef mapping: {mapped_count}")
            print(f"   Items without chef mapping: {unmapped_count}")
        
        print("\n=== END DEBUG REPORT ===")


if __name__ == "__main__":
    main() 