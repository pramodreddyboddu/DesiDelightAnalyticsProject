import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import db, Item
from src.main import create_app

app = create_app()

with app.app_context():
    print("=== CHECKING ITEM CLOVER IDS ===")
    # List items with missing clover_id
    missing_clover = Item.query.filter((Item.clover_id == None) | (Item.clover_id == '')).all()
    print(f"Items with missing clover_id: {len(missing_clover)}")
    for item in missing_clover:
        print(f"  ID: {item.id}, Name: '{item.name}', Tenant: {item.tenant_id}")
    # List items with duplicate names (case-insensitive)
    from collections import Counter
    all_items = Item.query.all()
    name_counts = Counter(item.name.strip().lower() for item in all_items)
    duplicates = [name for name, count in name_counts.items() if count > 1]
    print(f"\nItems with duplicate names: {len(duplicates)}")
    for name in duplicates:
        dups = [item for item in all_items if item.name.strip().lower() == name]
        print(f"  Name: '{name}' (Count: {len(dups)})")
        for item in dups:
            print(f"    ID: {item.id}, Clover ID: {item.clover_id}, Tenant: {item.tenant_id}")
    print("\n=== CHECK COMPLETE ===") 