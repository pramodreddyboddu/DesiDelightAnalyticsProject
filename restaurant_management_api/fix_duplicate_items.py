#!/usr/bin/env python3
"""
Fix duplicate clover_id entries in the item table
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import app, db
from src.models.item import Item
from sqlalchemy import text


def main():
    with app.app_context():
        print("=== FIXING DUPLICATE CLOVER_ID ENTRIES ===")
        
        # Find duplicate clover_ids
        print("Finding duplicate clover_id entries...")
        result = db.session.execute(text("""
            SELECT clover_id, COUNT(*) as count
            FROM item 
            WHERE clover_id IS NOT NULL
            GROUP BY clover_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """))
        
        duplicates = result.fetchall()
        
        if not duplicates:
            print("✅ No duplicate clover_id entries found!")
            return
        
        print(f"Found {len(duplicates)} clover_ids with duplicates:")
        for dup in duplicates[:10]:  # Show first 10
            print(f"   {dup[0]}: {dup[1]} entries")
        
        if len(duplicates) > 10:
            print(f"   ... and {len(duplicates) - 10} more")
        
        # Fix duplicates by keeping the one with the most complete data
        print("\nFixing duplicates...")
        fixed_count = 0
        
        for dup in duplicates:
            clover_id = dup[0]
            
            # Get all items with this clover_id
            items = Item.query.filter_by(clover_id=clover_id).all()
            
            if len(items) <= 1:
                continue
            
            # Sort by completeness (non-null fields, non-empty names, etc.)
            def completeness_score(item):
                score = 0
                if item.name and item.name.strip():
                    score += 10
                if item.price and item.price > 0:
                    score += 5
                if item.category and item.category != 'Uncategorized':
                    score += 3
                if item.description:
                    score += 2
                return score
            
            # Sort by completeness score (highest first)
            items.sort(key=completeness_score, reverse=True)
            
            # Keep the first (most complete) item, delete the rest
            keep_item = items[0]
            delete_items = items[1:]
            
            print(f"   Keeping: {keep_item.name} (ID: {keep_item.id})")
            for delete_item in delete_items:
                print(f"   Deleting: {delete_item.name} (ID: {delete_item.id})")
                db.session.delete(delete_item)
            
            fixed_count += len(delete_items)
        
        # Commit the changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully fixed {fixed_count} duplicate entries!")
            
            # Verify fix
            result = db.session.execute(text("""
                SELECT clover_id, COUNT(*) as count
                FROM item 
                WHERE clover_id IS NOT NULL
                GROUP BY clover_id 
                HAVING COUNT(*) > 1
            """))
            
            remaining_duplicates = result.fetchall()
            if not remaining_duplicates:
                print("✅ All duplicates have been resolved!")
            else:
                print(f"⚠️  {len(remaining_duplicates)} duplicates still remain")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing duplicates: {str(e)}")
            return
        
        # Show final stats
        total_items = Item.query.count()
        items_with_clover_id = Item.query.filter(Item.clover_id.isnot(None)).count()
        
        print(f"\n📊 FINAL STATS:")
        print(f"   Total items: {total_items}")
        print(f"   Items with clover_id: {items_with_clover_id}")
        print(f"   Items without clover_id: {total_items - items_with_clover_id}")
        
        print("\n=== DUPLICATE FIX COMPLETE ===")


if __name__ == "__main__":
    main() 