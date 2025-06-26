#!/usr/bin/env python3
"""
Debug script to check Clover inventory data and stockCount issues
"""

import requests
import json
from datetime import datetime, timedelta
import os

BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def login_and_get_session():
    """Login and get authenticated session"""
    session = requests.Session()
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def debug_clover_inventory(session):
    """Debug Clover inventory to see stockCount data"""
    print("\n" + "="*60)
    print("DEBUGGING CLOVER INVENTORY")
    print("="*60)
    
    # Get inventory from Clover
    response = session.get(f"{BASE_URL}/api/clover/inventory")
    if response.status_code != 200:
        print(f"❌ Failed to get inventory: {response.status_code}")
        return
    
    inventory_data = response.json()
    print(f"📊 Response structure: {type(inventory_data)}")
    print(f"📊 Response keys: {list(inventory_data.keys()) if isinstance(inventory_data, dict) else 'Not a dict'}")
    
    # Handle different response formats
    if isinstance(inventory_data, dict):
        items = inventory_data.get('items', [])
        total = inventory_data.get('total', 0)
    elif isinstance(inventory_data, list):
        items = inventory_data
        total = len(inventory_data)
    else:
        print(f"❌ Unexpected response format: {type(inventory_data)}")
        print(f"Response: {inventory_data}")
        return
    
    print(f"📊 Total items retrieved: {total}")
    
    if not items:
        print("❌ No items found")
        return
    
    # Analyze first few items
    zero_stock_count = 0
    non_zero_stock_count = 0
    
    for i, item in enumerate(items[:10]):  # Look at first 10 items
        print(f"\n--- Item {i+1} ---")
        print(f"ID: {item.get('id')}")
        print(f"Name: {item.get('name')}")
        print(f"Category: {item.get('category')}")
        print(f"Stock Count: {item.get('stockCount', item.get('quantity', 'N/A'))}")
        print(f"Price: {item.get('price')}")
        print(f"SKU: {item.get('sku')}")
        print(f"Product Code: {item.get('product_code')}")
        
        stock_count = item.get('stockCount', item.get('quantity', 0))
        if stock_count == 0:
            zero_stock_count += 1
        else:
            non_zero_stock_count += 1
    
    print(f"\n📊 Stock Count Summary:")
    print(f"  Items with zero stock: {zero_stock_count}")
    print(f"  Items with non-zero stock: {non_zero_stock_count}")
    print(f"  Total items analyzed: {len(items[:10])}")

def debug_raw_clover_items(session):
    """Debug raw Clover items endpoint to see full item data"""
    print("\n" + "="*60)
    print("DEBUGGING RAW CLOVER ITEMS")
    print("="*60)
    
    # Get raw items from Clover
    response = session.get(f"{BASE_URL}/api/clover/items?limit=5")
    if response.status_code != 200:
        print(f"❌ Failed to get raw items: {response.status_code}")
        return
    
    items_data = response.json()
    print(f"📊 Response structure: {type(items_data)}")
    
    if isinstance(items_data, dict):
        items = items_data.get('items', [])
    elif isinstance(items_data, list):
        items = items_data
    else:
        print(f"❌ Unexpected response format: {type(items_data)}")
        return
    
    print(f"📊 Raw items retrieved: {len(items)}")
    
    if not items:
        print("❌ No raw items found")
        return
    
    # Analyze first few raw items
    for i, item in enumerate(items[:3]):
        print(f"\n--- Raw Item {i+1} ---")
        print(f"Full item data:")
        print(json.dumps(item, indent=2, default=str))

def debug_inventory_sync(session):
    """Debug inventory sync process"""
    print("\n" + "="*60)
    print("DEBUGGING INVENTORY SYNC")
    print("="*60)
    
    # Trigger inventory sync
    response = session.post(f"{BASE_URL}/api/clover/sync/inventory")
    if response.status_code != 200:
        print(f"❌ Failed to sync inventory: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    sync_result = response.json()
    print(f"📊 Sync result: {sync_result}")
    
    # Check local inventory after sync
    response = session.get(f"{BASE_URL}/api/inventory")
    if response.status_code == 200:
        local_inventory = response.json()
        print(f"📊 Local inventory after sync: {len(local_inventory) if isinstance(local_inventory, list) else 'Not a list'}")
        
        # Check first few local items
        if isinstance(local_inventory, list):
            for i, item in enumerate(local_inventory[:3]):
                print(f"\n--- Local Item {i+1} ---")
                print(f"ID: {item.get('id')}")
                print(f"Name: {item.get('name')}")
                print(f"Category: {item.get('category')}")
                print(f"Quantity: {item.get('quantity')}")
                print(f"Clover ID: {item.get('clover_id')}")
        else:
            print(f"📊 Local inventory response: {local_inventory}")

def main():
    """Main debug function"""
    print("🔍 Starting Clover Inventory Debug...")
    
    # Login
    session = login_and_get_session()
    if not session:
        return
    
    # Debug inventory
    debug_clover_inventory(session)
    
    # Debug raw items
    debug_raw_clover_items(session)
    
    # Debug inventory sync
    debug_inventory_sync(session)
    
    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main() 