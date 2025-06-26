#!/usr/bin/env python3
"""
Test script for new Clover access token
"""
import requests

def test_clover_token(access_token):
    """Test a Clover access token"""
    merchant_id = "992206889881"
    
    print("=== Testing New Clover Access Token ===")
    print(f"Merchant ID: {merchant_id}")
    print(f"Access Token: {access_token[:10]}..." if access_token and len(access_token) > 10 else f"Access Token: {access_token}")
    print()
    
    # Test API connection
    url = f"https://api.clover.com/v3/merchants/{merchant_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("Testing API connection...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Clover API connection successful!")
            print(f"Merchant Name: {data.get('name', 'Unknown')}")
            print(f"Merchant ID: {data.get('id', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print("❌ ERROR: 401 Unauthorized - Invalid access token")
            print("Please check your access token")
            return False
        else:
            print(f"❌ ERROR: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Network error - {e}")
        return False

if __name__ == "__main__":
    # Replace this with your new access token
    new_access_token = "YOUR_NEW_ACCESS_TOKEN_HERE"
    
    if new_access_token == "YOUR_NEW_ACCESS_TOKEN_HERE":
        print("❌ Please replace 'YOUR_NEW_ACCESS_TOKEN_HERE' with your actual access token")
        print("Then run this script again.")
    else:
        success = test_clover_token(new_access_token)
        if success:
            print("\n🎉 Your new access token is working!")
            print("You can now update your .env file and restart the backend.")
        else:
            print("\n💡 The access token is still invalid.")
            print("Please check your Clover Developer Dashboard for the correct token.") 