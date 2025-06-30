#!/usr/bin/env python3
"""
Test API response directly
"""

import requests
import json
from datetime import datetime, timezone

def test_api_response():
    """Test the API response directly"""
    
    # Production API URL
    API_BASE_URL = "https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com/api"
    
    print("=== TESTING API RESPONSE ===\n")
    
    # Test chef performance endpoint
    print("Testing chef performance endpoint...")
    try:
        # Use today's date
        today = datetime.now(timezone.utc)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
        
        print(f"Request URL: {API_BASE_URL}/dashboard/chef-performance")
        print(f"Request params: {params}")
        
        response = requests.get(f"{API_BASE_URL}/dashboard/chef-performance", params=params, timeout=30)
        print(f"Status code: {response.status_code}")
        print(f"Response size: {len(response.content)} bytes")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nResponse data type: {type(data)}")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                if isinstance(data, dict):
                    chef_summary = data.get('chef_summary', [])
                    chef_performance = data.get('chef_performance', [])
                    
                    print(f"\nChef summary count: {len(chef_summary)}")
                    print(f"Chef performance count: {len(chef_performance)}")
                    
                    if chef_summary:
                        print("\nChef summary data:")
                        for chef in chef_summary:
                            print(f"  - {chef.get('name', 'Unknown')}: ${chef.get('total_revenue', 0)} ({chef.get('total_sales', 0)} sales)")
                    else:
                        print("❌ No chef summary data")
                        
                    if chef_performance:
                        print("\nChef performance data:")
                        for chef in chef_performance:
                            dishes = chef.get('dishes', [])
                            print(f"  - {chef.get('chef_name', 'Unknown')}: {len(dishes)} dishes")
                            for dish in dishes[:3]:  # Show first 3 dishes
                                print(f"    * {dish.get('item_name', 'Unknown')}: ${dish.get('revenue', 0)} ({dish.get('count', 0)} sold)")
                    else:
                        print("❌ No chef performance data")
                else:
                    print(f"❌ Unexpected response type: {type(data)}")
                    print(f"Response: {data}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {str(e)}")
                print(f"Raw response: {response.text}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_api_response() 