#!/usr/bin/env python3
"""
Test production API endpoints to debug staff performance
"""

import requests
import json
from datetime import datetime, timezone

# Production API URL
API_BASE_URL = "https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com/api"

def test_production_api():
    """Test production API endpoints"""
    
    print("=== TESTING PRODUCTION API ===\n")
    
    # Test 1: Check if API is accessible
    print("1. Testing API accessibility...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"   Health check: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API is accessible")
        else:
            print(f"   ❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error connecting to API: {str(e)}")
        return
    
    # Test 2: Test chef performance endpoint
    print("\n2. Testing chef performance endpoint...")
    try:
        # Use today's date
        today = datetime.now(timezone.utc)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        response = requests.get(f"{API_BASE_URL}/dashboard/chef-performance", params=params, timeout=30)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Got response with keys: {list(data.keys())}")
            
            chef_summary = data.get('chef_summary', [])
            chef_performance = data.get('chef_performance', [])
            
            print(f"   Chef summary count: {len(chef_summary)}")
            print(f"   Chef performance count: {len(chef_performance)}")
            
            if chef_summary:
                print("\n   Chef summary data:")
                for chef in chef_summary:
                    print(f"     - {chef.get('name', 'Unknown')}: ${chef.get('total_revenue', 0)} ({chef.get('total_sales', 0)} sales)")
            else:
                print("   ❌ No chef summary data")
                
            if chef_performance:
                print("\n   Chef performance data:")
                for chef in chef_performance:
                    dishes = chef.get('dishes', [])
                    print(f"     - {chef.get('chef_name', 'Unknown')}: {len(dishes)} dishes")
                    for dish in dishes[:3]:  # Show first 3 dishes
                        print(f"       * {dish.get('item_name', 'Unknown')}: ${dish.get('revenue', 0)} ({dish.get('count', 0)} sold)")
            else:
                print("   ❌ No chef performance data")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing chef performance: {str(e)}")
    
    # Test 3: Test chefs list endpoint
    print("\n3. Testing chefs list endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/dashboard/chefs", timeout=10)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            chefs = response.json()
            print(f"   ✅ Found {len(chefs)} chefs")
            for chef in chefs[:5]:  # Show first 5 chefs
                print(f"     - {chef.get('name', 'Unknown')} (ID: {chef.get('id', 'Unknown')})")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing chefs list: {str(e)}")
    
    # Test 4: Test data source configuration
    print("\n4. Testing data source configuration...")
    try:
        response = requests.get(f"{API_BASE_URL}/dashboard/data-source-config", timeout=10)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ Data source config: {config}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error testing data source config: {str(e)}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_production_api() 