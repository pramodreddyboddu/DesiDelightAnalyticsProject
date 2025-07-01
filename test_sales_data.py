import requests
import json

# Test the staff performance endpoint to see what data we have
API_URL = "https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com/api/dashboard/chef-performance"

# Test with today's date
params = {
    "start_date": "2025-06-30T00:00:00.000Z",
    "end_date": "2025-06-30T23:59:59.000Z"
}

print("Testing staff performance analytics...")
print(f"Date range: {params['start_date']} to {params['end_date']}")

try:
    response = requests.get(API_URL, params=params, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Staff Performance Data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n" + "="*50)

# Also test the sales count endpoint
print("Testing sales count...")
try:
    sales_response = requests.get("https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com/api/dashboard/overview", timeout=30)
    print(f"Sales Status: {sales_response.status_code}")
    
    if sales_response.status_code == 200:
        sales_data = sales_response.json()
        print("✅ Sales Overview Data:")
        print(json.dumps(sales_data, indent=2))
    else:
        print(f"❌ Sales Error: {sales_response.text}")
        
except Exception as e:
    print(f"❌ Sales request failed: {e}") 