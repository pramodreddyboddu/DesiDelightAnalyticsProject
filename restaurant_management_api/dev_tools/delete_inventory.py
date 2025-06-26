import requests

# First, login to get the session cookie
login_url = "http://localhost:5000/api/auth/login"
login_data = {
    "username": "admin",
    "password": "admin123"
}

# Create a session to maintain cookies
session = requests.Session()

# Login
login_response = session.post(login_url, json=login_data)
print(f"Login Status Code: {login_response.status_code}")
print(f"Login Response: {login_response.text}")

if login_response.status_code == 200:
    # Now make the delete request using the same session
    delete_url = "http://localhost:5000/api/admin/force-delete-inventory"
    delete_response = session.delete(delete_url)
    print(f"\nDelete Status Code: {delete_response.status_code}")
    print(f"Delete Response: {delete_response.text}")
else:
    print("Login failed. Please check your credentials.") 