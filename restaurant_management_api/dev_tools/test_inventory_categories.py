#!/usr/bin/env python3
"""
Test script to check inventory data and category mapping
"""
import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000/api"
SESSION_COOKIE = "plateiq_session=c14b776b-7bd6-436a-95d6-f2743084261b.IA92esgy3jId299M7mVhZBmAv9c"

def test_inventory_data():
    """Test inventory data endpoint"""
    print("Testing inventory data...")
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': SESSION_COOKIE
    }
    
    try:
        # Test inventory endpoint
        response = requests.get(f"{BASE_URL}/inventory", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            print(f"Total items: {len(items)}")
            
            # Show first 5 items with their categories
            print("\nFirst 5 items with categories:")
            for i, item in enumerate(items[:5]):
                print(f"{i+1}. {item.get('name', 'Unknown')} - Category: {item.get('category', 'Uncategorized')}")
            
            # Count items by category
            categories = {}
            for item in items:
                category = item.get('category', 'Uncategorized')
                categories[category] = categories.get(category, 0) + 1
            
            print(f"\nCategory breakdown:")
            for category, count in sorted(categories.items()):
                print(f"  {category}: {count} items")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_categories():
    """Test categories endpoint"""
    print("\nTesting categories endpoint...")
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': SESSION_COOKIE
    }
    
    try:
        response = requests.get(f"{BASE_URL}/inventory/categories", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            print(f"Total categories: {len(categories)}")
            
            print("\nCategories:")
            for cat in categories:
                print(f"  - {cat}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_clover_debug():
    """Test Clover debug endpoint"""
    print("\nTesting Clover debug endpoint...")
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': SESSION_COOKIE
    }
    
    try:
        response = requests.get(f"{BASE_URL}/clover/debug/items", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            debug_items = data.get('debug_items', [])
            print(f"Debug items: {len(debug_items)}")
            
            for i, item in enumerate(debug_items):
                print(f"\nItem {i+1}:")
                print(f"  Name: {item.get('name', 'Unknown')}")
                print(f"  ID: {item.get('id', 'Unknown')}")
                print(f"  Categories: {json.dumps(item.get('categories', {}), indent=2)}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=== Inventory Category Mapping Test ===")
    print(f"Time: {datetime.now()}")
    
    test_inventory_data()
    test_categories()
    test_clover_debug()
    
    print("\n=== Test Complete ===") 