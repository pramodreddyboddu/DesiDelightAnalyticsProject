import requests
from datetime import datetime, timedelta

# Create a session to maintain cookies
session = requests.Session()

# Login
login_url = "http://localhost:5000/api/auth/login"
login_data = {
    "username": "admin",
    "password": "admin123"
}

# Login
login_response = session.post(login_url, json=login_data)
print(f"Login Status Code: {login_response.status_code}")
print(f"Login Response: {login_response.text}")

if login_response.status_code == 200:
    # Get current date and date from 1 year ago
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    # Format dates for API
    start_date_str = start_date.isoformat() + 'Z'
    end_date_str = end_date.isoformat() + 'Z'
    
    # Test deletion for each data type
    data_types = ['sales', 'inventory', 'expenses', 'chef_mapping']
    
    for data_type in data_types:
        print(f"\nTesting deletion for {data_type}...")
        
        # First get current stats
        stats_url = "http://localhost:5000/api/admin/data-stats"
        stats_response = session.get(stats_url)
        print(f"Current stats: {stats_response.text}")
        
        # Delete data
        delete_url = "http://localhost:5000/api/admin/delete-data"
        delete_data = {
            "data_type": data_type,
            "start_date": start_date_str,
            "end_date": end_date_str
        }
        
        delete_response = session.delete(delete_url, json=delete_data)
        print(f"Delete Status Code: {delete_response.status_code}")
        print(f"Delete Response: {delete_response.text}")
        
        # Get updated stats
        stats_response = session.get(stats_url)
        print(f"Updated stats: {stats_response.text}")
        
        print("-" * 50)
else:
    print("Login failed. Please check your credentials.") 