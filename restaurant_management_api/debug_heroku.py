#!/usr/bin/env python3
"""
Simple debug script for Heroku production database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import app, db
from sqlalchemy import text

def main():
    with app.app_context():
        print("=== PRODUCTION DATABASE DEBUG REPORT ===")
        try:
            # Print all table names in the current database
            print("\n📋 Listing all tables in the database:")
            result = db.session.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            for t in tables:
                print(f"   - {t[0]}")
        except Exception as e:
            print(f"❌ Error listing tables: {e}")
            import traceback
            traceback.print_exc()
            return

        # Direct SQL queries to avoid model import issues
        try:
            # Basic counts
            result = db.session.execute(text("SELECT COUNT(*) as count FROM item"))
            total_items = result.fetchone()[0]
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM chef"))
            total_chefs = result.fetchone()[0]
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM chef_dish_mapping"))
            total_mappings = result.fetchone()[0]
            
            result = db.session.execute(text("SELECT COUNT(*) as count FROM sale"))
            total_sales = result.fetchone()[0]
            
            print(f"\n📊 DATABASE COUNTS:")
            print(f"   Items: {total_items}")
            print(f"   Chefs: {total_chefs}")
            print(f"   Chef Mappings: {total_mappings}")
            print(f"   Sales Records: {total_sales}")
            
            # Sample mappings
            print(f"\n🔗 SAMPLE CHEF MAPPINGS (first 5):")
            result = db.session.execute(text("""
                SELECT cdm.id, c.name as chef_name, i.name as item_name 
                FROM chef_dish_mapping cdm
                LEFT JOIN chef c ON cdm.chef_id = c.id
                LEFT JOIN item i ON cdm.item_id = i.id
                LIMIT 5
            """))
            mappings = result.fetchall()
            for m in mappings:
                print(f"   Mapping {m[0]}: {m[1] or 'Unknown Chef'} -> {m[2] or 'Unknown Item'}")
            
            # Check for Butter Chicken specifically
            print(f"\n🍗 LOOKING FOR BUTTER CHICKEN:")
            result = db.session.execute(text("""
                SELECT id, name FROM item 
                WHERE name LIKE '%Butter Chicken%' OR name LIKE '%ButterChicken%'
            """))
            butter_items = result.fetchall()
            if butter_items:
                for item in butter_items:
                    print(f"   Found: {item[1]} (ID: {item[0]})")
                    result = db.session.execute(text("""
                        SELECT c.name FROM chef_dish_mapping cdm
                        LEFT JOIN chef c ON cdm.chef_id = c.id
                        WHERE cdm.item_id = :item_id
                    """), {"item_id": item[0]})
                    mapping = result.fetchone()
                    if mapping:
                        print(f"     Mapped to: {mapping[0] or 'Unknown'}")
                    else:
                        print(f"     ❌ NOT MAPPED TO ANY CHEF!")
            else:
                print("   ❌ No Butter Chicken items found!")
            
            # Check unmapped sales items
            print(f"\n❌ SALES ITEMS WITHOUT CHEF MAPPING:")
            result = db.session.execute(text("""
                SELECT DISTINCT s.item_id, i.name
                FROM sale s
                LEFT JOIN item i ON s.item_id = i.id
                WHERE s.item_id NOT IN (SELECT item_id FROM chef_dish_mapping)
                LIMIT 10
            """))
            unmapped = result.fetchall()
            
            if unmapped:
                print(f"   Found {len(unmapped)} unmapped items:")
                for item_id, name in unmapped:
                    print(f"     {name or 'Unknown'} (ID: {item_id})")
            else:
                print("   ✅ All sales items are mapped!")
            
            # Check tenant consistency
            print(f"\n🏢 TENANT CONSISTENCY CHECK:")
            result = db.session.execute(text("SELECT COUNT(*) as count FROM tenants"))
            total_tenants = result.fetchone()[0]
            print(f"   Total Tenants: {total_tenants}")
            
            result = db.session.execute(text("""
                SELECT t.name, COUNT(cdm.id) as mapping_count
                FROM tenants t
                LEFT JOIN chef_dish_mapping cdm ON t.id = cdm.tenant_id
                GROUP BY t.id, t.name
            """))
            tenant_mappings = result.fetchall()
            for tenant_name, mapping_count in tenant_mappings:
                print(f"   {tenant_name}: {mapping_count} mappings")
            
            print(f"\n=== END REPORT ===")
            
        except Exception as e:
            print(f"❌ Error during database query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 