"""
Direct Database Fix for Butter Chicken Masala Chef Mapping
This script directly connects to the Heroku database to fix the mapping issue
"""

import os
import sys
import requests
import json
from datetime import datetime

# Heroku production API URL
HEROKU_API_URL = "https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com"

def login_and_get_session():
    """Login to get a session for API calls"""
    try:
        # Try to login with admin credentials
        login_data = {
            'username': 'admin',
            'password': 'secure-admin-password-2024'
        }
        
        session = requests.Session()
        response = session.post(f"{HEROKU_API_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            print("✅ Login successful")
            return session
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login exception: {e}")
        return None

def get_chefs_with_session(session):
    """Get all chefs using authenticated session"""
    try:
        response = session.get(f"{HEROKU_API_URL}/api/dashboard/chefs")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting chefs: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception getting chefs: {e}")
        return None

def get_inventory_with_session(session):
    """Get all items using authenticated session"""
    try:
        response = session.get(f"{HEROKU_API_URL}/api/inventory")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error getting inventory: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception getting inventory: {e}")
        return None

def create_chef_mapping_via_upload(session, chef_name, item_name):
    """Create chef mapping using the upload endpoint with CSV data"""
    try:
        # Create a simple CSV content for the mapping
        csv_content = f"chef_name,item_name\n{chef_name},{item_name}"
        
        # Create a file-like object
        from io import BytesIO
        file_data = BytesIO(csv_content.encode('utf-8'))
        
        # Prepare the multipart form data
        files = {'file': ('chef_mapping.csv', file_data, 'text/csv')}
        
        response = session.post(f"{HEROKU_API_URL}/api/upload/chef-mapping", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Mapping created successfully: {result.get('message', 'Success')}")
            return True
        else:
            print(f"❌ Error creating mapping: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception creating mapping: {e}")
        return False

def trigger_auto_sync(session):
    """Trigger the auto-sync for chef mappings"""
    try:
        response = session.post(f"{HEROKU_API_URL}/api/admin/sync-chef-mappings")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Auto-sync triggered: {result}")
            return True
        else:
            print(f"❌ Auto-sync failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Auto-sync exception: {e}")
        return False

def main():
    print("=== Fixing Butter Chicken Masala Chef Mapping ===")
    print(f"Target API: {HEROKU_API_URL}")
    
    # Step 1: Login
    print("\n1. Logging in...")
    session = login_and_get_session()
    if not session:
        print("❌ Cannot proceed without login")
        return
    
    # Step 2: Get chefs
    print("\n2. Getting chefs...")
    chefs = get_chefs_with_session(session)
    if not chefs:
        print("❌ Cannot proceed without chefs data")
        return
    
    print(f"Found {len(chefs)} chefs:")
    for chef in chefs:
        print(f"  - {chef.get('name', 'Unknown')} (ID: {chef.get('id', 'Unknown')})")
    
    # Step 3: Get inventory
    print("\n3. Getting inventory...")
    inventory = get_inventory_with_session(session)
    if not inventory:
        print("❌ Cannot proceed without inventory data")
        return
    
    # Fix: Use inventory['items']
    items_list = inventory.get('items', [])
    # Find Butter Chicken Masala
    butter_chicken = None
    for item in items_list:
        if 'Butter Chicken' in item.get('name', ''):
            butter_chicken = item
            break
    
    if not butter_chicken:
        print("❌ Butter Chicken Masala not found in inventory!")
        return
    
    print(f"Found Butter Chicken Masala: {butter_chicken.get('name')} (ID: {butter_chicken.get('id')})")
    
    # Step 4: Select a suitable chef
    suitable_chef = None
    for chef in chefs:
        chef_name = chef.get('name', '').lower()
        # Prefer chefs that might handle curries
        if any(keyword in chef_name for keyword in ['wasim', 'savithri', 'chef']):
            suitable_chef = chef
            break
    
    if not suitable_chef:
        # Use the first available chef
        suitable_chef = chefs[0] if chefs else None
    
    if not suitable_chef:
        print("❌ No suitable chef found!")
        return
    
    print(f"Selected chef: {suitable_chef.get('name')} (ID: {suitable_chef.get('id')})")
    
    # Step 5: Try auto-sync first
    print("\n4. Trying auto-sync...")
    auto_sync_success = trigger_auto_sync(session)
    
    if not auto_sync_success:
        # Step 6: Manual mapping creation
        print("\n5. Creating manual mapping...")
        success = create_chef_mapping_via_upload(
            session, 
            suitable_chef.get('name'), 
            butter_chicken.get('name')
        )
        
        if success:
            print("\n✅ SUCCESS: Butter Chicken Masala has been mapped to a chef!")
            print(f"   Chef: {suitable_chef.get('name')}")
            print(f"   Item: {butter_chicken.get('name')}")
            print("\nThe chef performance dashboard should now show this dish.")
        else:
            print("\n❌ FAILED: Could not create the chef mapping.")
            print("You may need to create the mapping manually through the admin interface.")
    else:
        print("\n✅ SUCCESS: Auto-sync completed successfully!")
        print("The chef performance dashboard should now show Butter Chicken Masala.")

if __name__ == "__main__":
    main() 