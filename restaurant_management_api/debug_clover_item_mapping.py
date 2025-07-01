#!/usr/bin/env python3
"""
Debug script: Check for Clover sales item IDs missing from local item table, and for items missing chef mappings.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import app, db
from src.services.clover_service import CloverService
from src.models.item import Item
from src.models.chef_dish_mapping import ChefDishMapping
from src.models.chef import Chef


def main():
    with app.app_context():
        print("=== CLOVER ITEM MAPPING DEBUG ===")
        clover_service = CloverService()
        # Get recent orders from Clover
        print("Fetching recent orders from Clover API...")
        orders = clover_service.get_orders()
        clover_item_ids = set()
        for order in orders:
            line_items = order.get('lineItems', {}).get('elements', [])
            for li in line_items:
                item = li.get('item', {})
                clover_id = item.get('id')
                name = item.get('name', 'Unknown')
                if clover_id:
                    clover_item_ids.add((clover_id, name))
        print(f"Found {len(clover_item_ids)} unique Clover item IDs in recent sales.")

        # Check for each Clover item ID if it exists in local item table
        missing_in_local = []
        missing_chef_mapping = []
        for clover_id, name in clover_item_ids:
            local_item = Item.query.filter_by(clover_id=clover_id).first()
            if not local_item:
                missing_in_local.append((clover_id, name))
            else:
                # Check for chef mapping
                mapping = ChefDishMapping.query.filter_by(item_id=local_item.id).first()
                if not mapping:
                    missing_chef_mapping.append((clover_id, name, local_item.id))
        print(f"\nItems in Clover sales missing from local item table: {len(missing_in_local)}")
        for clover_id, name in missing_in_local[:10]:
            print(f"  - {name} (Clover ID: {clover_id})")
        if len(missing_in_local) > 10:
            print(f"  ... and {len(missing_in_local)-10} more")

        print(f"\nItems in local item table (by Clover ID) but missing chef mapping: {len(missing_chef_mapping)}")
        for clover_id, name, local_id in missing_chef_mapping[:10]:
            print(f"  - {name} (Clover ID: {clover_id}, Local ID: {local_id})")
        if len(missing_chef_mapping) > 10:
            print(f"  ... and {len(missing_chef_mapping)-10} more")

        print("\n=== END DEBUG ===")

if __name__ == "__main__":
    main() 