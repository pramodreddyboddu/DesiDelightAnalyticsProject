#!/usr/bin/env python3
"""
Simple debug script for Heroku production database
"""
import sys
import os
sys.path.append('src')

from src import create_app
from src.models import db, ChefDishMapping, Chef, Item, Sale

def main():
    app = create_app()
    with app.app_context():
        print("=== PRODUCTION DATABASE DEBUG REPORT ===")
        
        # Basic counts
        total_items = Item.query.count()
        total_chefs = Chef.query.count()
        total_mappings = ChefDishMapping.query.count()
        total_sales = Sale.query.count()
        
        print(f"📊 DATABASE COUNTS:")
        print(f"   Items: {total_items}")
        print(f"   Chefs: {total_chefs}")
        print(f"   Chef Mappings: {total_mappings}")
        print(f"   Sales Records: {total_sales}")
        
        # Sample mappings
        print(f"\n🔗 SAMPLE CHEF MAPPINGS (first 5):")
        mappings = ChefDishMapping.query.limit(5).all()
        for m in mappings:
            chef = Chef.query.get(m.chef_id)
            item = Item.query.get(m.item_id)
            print(f"   Mapping {m.id}: {chef.name if chef else 'Unknown Chef'} -> {item.name if item else 'Unknown Item'}")
        
        # Check for Butter Chicken specifically
        print(f"\n🍗 LOOKING FOR BUTTER CHICKEN:")
        butter_items = Item.query.filter(Item.name.like('%Butter Chicken%')).all()
        if butter_items:
            for item in butter_items:
                print(f"   Found: {item.name} (ID: {item.id})")
                mapping = ChefDishMapping.query.filter_by(item_id=item.id).first()
                if mapping:
                    chef = Chef.query.get(mapping.chef_id)
                    print(f"     Mapped to: {chef.name if chef else 'Unknown'}")
                else:
                    print(f"     ❌ NOT MAPPED TO ANY CHEF!")
        else:
            print("   ❌ No Butter Chicken items found!")
        
        # Check unmapped sales items
        print(f"\n❌ SALES ITEMS WITHOUT CHEF MAPPING:")
        sales_item_ids = set(s.item_id for s in Sale.query.all())
        mapped_item_ids = set(m.item_id for m in ChefDishMapping.query.all())
        unmapped = sales_item_ids - mapped_item_ids
        
        if unmapped:
            print(f"   Found {len(unmapped)} unmapped items:")
            for item_id in list(unmapped)[:5]:
                item = Item.query.get(item_id)
                print(f"     {item.name if item else 'Unknown'} (ID: {item_id})")
            if len(unmapped) > 5:
                print(f"     ... and {len(unmapped)-5} more")
        else:
            print("   ✅ All sales items are mapped!")
        
        print(f"\n=== END REPORT ===")

if __name__ == "__main__":
    main() 