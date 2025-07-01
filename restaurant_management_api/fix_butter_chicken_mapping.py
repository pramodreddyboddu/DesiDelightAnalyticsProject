"""
Fix Butter Chicken Masala Chef Mapping
This script will create the missing chef mapping for Butter Chicken Masala
"""

import requests
import json

# Heroku production API URL
HEROKU_API_URL = "https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com"

def get_chefs():
    """Get all chefs from the API"""
    try:
        response = requests.get(f"{HEROKU_API_URL}/api/dashboard/chefs")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting chefs: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception getting chefs: {e}")
        return None

def get_items():
    """Get all items from the API"""
    try:
        response = requests.get(f"{HEROKU_API_URL}/api/inventory")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting items: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception getting items: {e}")
        return None

def create_chef_mapping(chef_id, item_id, tenant_id):
    """Create a chef mapping via API"""
    try:
        mapping_data = {
            "chef_id": chef_id,
            "item_id": item_id,
            "tenant_id": tenant_id,
            "is_active": True
        }
        
        response = requests.post(
            f"{HEROKU_API_URL}/api/chef-mappings",
            json=mapping_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            print(f"Successfully created mapping: Chef {chef_id} -> Item {item_id}")
            return True
        else:
            print(f"Error creating mapping: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exception creating mapping: {e}")
        return False

def main():
    print("=== Fixing Butter Chicken Masala Chef Mapping ===")
    
    # Get chefs
    print("\n1. Getting chefs...")
    chefs_data = get_chefs()
    if not chefs_data:
        print("Failed to get chefs")
        return
    
    print(f"Found {len(chefs_data)} chefs:")
    for chef in chefs_data:
        print(f"  - {chef.get('name', 'Unknown')} (ID: {chef.get('id', 'Unknown')})")
    
    # Get items
    print("\n2. Getting items...")
    items_data = get_items()
    if not items_data:
        print("Failed to get items")
        return
    
    # Find Butter Chicken Masala
    butter_chicken = None
    for item in items_data:
        if 'Butter Chicken' in item.get('name', ''):
            butter_chicken = item
            break
    
    if not butter_chicken:
        print("Butter Chicken Masala not found in items!")
        return
    
    print(f"Found Butter Chicken Masala: {butter_chicken.get('name')} (ID: {butter_chicken.get('id')})")
    
    # Find a suitable chef (preferably one that handles curries)
    suitable_chef = None
    for chef in chefs_data:
        chef_name = chef.get('name', '').lower()
        if any(keyword in chef_name for keyword in ['curry', 'chef', 'wasim', 'savithri']):
            suitable_chef = chef
            break
    
    if not suitable_chef:
        # Use the first available chef
        suitable_chef = chefs_data[0] if chefs_data else None
    
    if not suitable_chef:
        print("No suitable chef found!")
        return
    
    print(f"Selected chef: {suitable_chef.get('name')} (ID: {suitable_chef.get('id')})")
    
    # Create the mapping
    print("\n3. Creating chef mapping...")
    tenant_id = "31a6a0fa-3d86-4b03-ad26-44503189d3d4"  # Default tenant ID from logs
    
    success = create_chef_mapping(
        chef_id=suitable_chef.get('id'),
        item_id=butter_chicken.get('id'),
        tenant_id=tenant_id
    )
    
    if success:
        print("\n✅ SUCCESS: Butter Chicken Masala has been mapped to a chef!")
        print(f"   Chef: {suitable_chef.get('name')}")
        print(f"   Item: {butter_chicken.get('name')}")
        print("\nThe chef performance dashboard should now show this dish.")
    else:
        print("\n❌ FAILED: Could not create the chef mapping.")
        print("You may need to create the mapping manually through the admin interface.")

if __name__ == "__main__":
    main() 