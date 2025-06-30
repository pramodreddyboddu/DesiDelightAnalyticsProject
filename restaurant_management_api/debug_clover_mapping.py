#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src import create_app
from src.models import db, ChefDishMapping, Chef, Item, Sale
from src.services.clover_service import CloverService

def debug_clover_mapping():
    app = create_app()
    
    with app.app_context():
        print("=== DEBUGGING CLOVER ITEM MAPPING ISSUE ===")
        
        # Check local items and their clover_ids
        local_items = Item.query.all()
        print(f"Total local items: {len(local_items)}")
        
        # Create item_id_map like in the dashboard service
        item_id_map = {item.clover_id: item.id for item in local_items}
        print(f"Items with clover_id: {len(item_id_map)}")
        
        # Show sample local items
        print(f"\nSample local items:")
        for i, item in enumerate(local_items[:10]):
            print(f"  {i+1}. ID: {item.id}, Name: '{item.name}', Clover ID: '{item.clover_id}', Tenant: {item.tenant_id}")
        
        # Get Clover items
        clover_service = CloverService()
        try:
            clover_items = clover_service.get_items()
            print(f"\nTotal Clover items: {len(clover_items)}")
            
            # Show sample Clover items
            print(f"\nSample Clover items:")
            for i, item in enumerate(clover_items[:10]):
                print(f"  {i+1}. Clover ID: '{item.get('id')}', Name: '{item.get('name')}'")
            
            # Check mapping
            mapped_count = 0
            unmapped_count = 0
            unmapped_items = []
            
            for clover_item in clover_items:
                clover_id = clover_item.get('id')
                if clover_id in item_id_map:
                    mapped_count += 1
                else:
                    unmapped_count += 1
                    if len(unmapped_items) < 10:
                        unmapped_items.append({
                            'clover_id': clover_id,
                            'name': clover_item.get('name', 'Unknown')
                        })
            
            print(f"\nMapping results:")
            print(f"  Mapped Clover items: {mapped_count}")
            print(f"  Unmapped Clover items: {unmapped_count}")
            
            if unmapped_items:
                print(f"\nSample unmapped Clover items:")
                for item in unmapped_items:
                    print(f"  Clover ID: '{item['clover_id']}', Name: '{item['name']}'")
            
            # Check if there are any items with sales
            if clover_items:
                # Get some orders to see what items are actually being sold
                orders = clover_service.get_orders()
                print(f"\nTotal Clover orders: {len(orders)}")
                
                sold_items = set()
                for order in orders[:10]:  # Check first 10 orders
                    line_items = order.get('lineItems', {}).get('elements', [])
                    for line_item in line_items:
                        item = line_item.get('item', {})
                        sold_items.add(item.get('id'))
                
                print(f"Unique items sold in sample orders: {len(sold_items)}")
                
                # Check which sold items are mapped
                sold_mapped = 0
                sold_unmapped = 0
                for sold_item_id in sold_items:
                    if sold_item_id in item_id_map:
                        sold_mapped += 1
                    else:
                        sold_unmapped += 1
                
                print(f"  Sold items that are mapped: {sold_mapped}")
                print(f"  Sold items that are NOT mapped: {sold_unmapped}")
                
        except Exception as e:
            print(f"Error getting Clover data: {str(e)}")
        
        # Check chef mappings
        chef_mappings = ChefDishMapping.query.all()
        print(f"\nTotal chef mappings: {len(chef_mappings)}")
        
        # Check which items have chef mappings
        mapped_item_ids = set(mapping.item_id for mapping in chef_mappings)
        print(f"Local items with chef mappings: {len(mapped_item_ids)}")
        
        # Check if mapped items have clover_ids
        mapped_items_with_clover = 0
        for item_id in mapped_item_ids:
            item = Item.query.get(item_id)
            if item and item.clover_id:
                mapped_items_with_clover += 1
        
        print(f"Chef-mapped items that have clover_id: {mapped_items_with_clover}")

if __name__ == "__main__":
    debug_clover_mapping() 