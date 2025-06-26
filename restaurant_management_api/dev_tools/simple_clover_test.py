#!/usr/bin/env python3
"""
Simple script to test Clover API credentials without .env file
"""
import os
import requests

def test_clover_credentials():
    """Test Clover API credentials"""
    # Set credentials manually
    merchant_id = "992206889881"
    access_token = "e6e48423-d223-f206-0ab2-572cce38bff4"  # Replace this with your real token
    
    print("=== Clover API Credentials Test ===")
    print(f"Merchant ID: {merchant_id}")
    print(f"Access Token: {access_token[:10]}..." if access_token and len(access_token) > 10 else f"Access Token: {access_token}")
    print()
    
    if access_token == 'your_actual_clover_access_token_here':
        print("❌ ERROR: Access token is still the placeholder value")
        print("Please replace 'your_actual_clover_access_token_here' with your real access token")
        print("\nTo fix this:")
        print("1. Get your access token from Clover Developer Dashboard")
        print("2. Replace the access_token variable in this script")
        print("3. Run this script again to test")
        return False
    
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
    success = test_clover_credentials()
    if success:
        print("\n🎉 Your Clover credentials are working correctly!")
        print("You can now update your .env file and restart the backend.")
    else:
        print("\n💡 Next steps:")
        print("1. Get your access token from Clover Developer Dashboard")
        print("2. Update the access_token variable in this script")
        print("3. Run this script again to test")
        print("4. Once working, update your .env file and restart the backend") 