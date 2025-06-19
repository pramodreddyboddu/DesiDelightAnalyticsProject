import requests

# Create a session to maintain cookies
session = requests.Session()

# Test login
print("Testing login...")
login_response = session.post('http://localhost:5000/api/auth/login', 
                             json={'username': 'admin', 'password': 'admin123'})
print(f"Login status: {login_response.status_code}")
print(f"Login response: {login_response.text}")

# Check session cookies
print(f"\nSession cookies: {dict(session.cookies)}")

# Test inventory endpoint
print("\nTesting inventory endpoint...")
inventory_response = session.get('http://localhost:5000/api/inventory')
print(f"Inventory status: {inventory_response.status_code}")
print(f"Inventory response: {inventory_response.text}")

# Test chef performance endpoint for comparison
print("\nTesting chef performance endpoint...")
chef_response = session.get('http://localhost:5000/api/dashboard/chef-performance')
print(f"Chef performance status: {chef_response.status_code}")
print(f"Chef performance response: {chef_response.text[:200]}")

# Test auth/me endpoint
print("\nTesting auth/me endpoint...")
me_response = session.get('http://localhost:5000/api/auth/me')
print(f"Auth/me status: {me_response.status_code}")
print(f"Auth/me response: {me_response.text}") 