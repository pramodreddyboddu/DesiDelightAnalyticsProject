#!/usr/bin/env python3
"""
Fix Clover item sync: Update local item table with current Clover items
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
        print("=== CLOVER ITEM SYNC FIX ===")
        
        # Initialize Clover service
        clover_config = CloverConfig(
            merchant_id=os.getenv('CLOVER_MERCHANT_ID', ''),
            access_token=os.getenv('CLOVER_ACCESS_TOKEN', '')
        )
        clover_service = CloverService(clover_config)
        
        print("Fetching items from Clover...")
        clover_items = clover_service.get_items()
        
        if not clover_items:
            print("❌ No items found from Clover API")
            return
        
        print(f"Found {len(clover_items)} items in Clover")
        
        # Get existing local items
        local_items = Item.query.all()
        local_clover_ids = {item.clover_id for item in local_items if item.clover_id}
        print(f"Local database has {len(local_items)} items, {len(local_clover_ids)} with clover_id")
        
        # Process Clover items
        updated_count = 0
        added_count = 0
        unchanged_count = 0
        
        for clover_item in clover_items:
            clover_id = clover_item.get('id')
            name = clover_item.get('name', 'Unknown')
            price = clover_item.get('price', 0)
            
            if not clover_id:
                continue
                
            # Check if item exists locally
            local_item = Item.query.filter_by(clover_id=clover_id).first()
            
            if local_item:
                # Update existing item
                if (local_item.name != name or 
                    local_item.price != price):
                    local_item.name = name
                    local_item.price = price
                    updated_count += 1
                    print(f"   🔄 Updated: {name} (ID: {clover_id})")
                else:
                    unchanged_count += 1
            else:
                # Add new item
                new_item = Item(
                    name=name,
                    price=price,
                    clover_id=clover_id,
                    category='Uncategorized'
                )
                db.session.add(new_item)
                added_count += 1
                print(f"   ➕ Added: {name} (ID: {clover_id})")
        
        # Commit changes
        try:
            db.session.commit()
            print(f"\n✅ SYNC COMPLETE:")
            print(f"   Items updated: {updated_count}")
            print(f"   Items added: {added_count}")
            print(f"   Items unchanged: {unchanged_count}")
            print(f"   Total items in local DB: {Item.query.count()}")
            
            # Check chef mappings
            total_items = Item.query.count()
            mapped_items = ChefDishMapping.query.count()
            print(f"\n📊 CHEF MAPPING STATUS:")
            print(f"   Total items: {total_items}")
            print(f"   Items with chef mapping: {mapped_items}")
            print(f"   Items without chef mapping: {total_items - mapped_items}")
            
            if total_items - mapped_items > 0:
                print(f"\n⚠️  WARNING: {total_items - mapped_items} items need chef mappings!")
                print("   You may need to re-upload your chef mapping file.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during sync: {str(e)}")
            return
        
        print("\n=== SYNC COMPLETE ===")


if __name__ == "__main__":
    main() 