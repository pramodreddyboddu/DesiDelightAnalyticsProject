#!/usr/bin/env python3
"""
Simple script to test Clover API credentials
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_clover_credentials():
    """Test Clover API credentials"""
    merchant_id = os.getenv('CLOVER_MERCHANT_ID')
    access_token = os.getenv('CLOVER_ACCESS_TOKEN')
    
    print("=== Clover API Credentials Test ===")
    print(f"Merchant ID: {merchant_id}")
    print(f"Access Token: {access_token[:10]}..." if access_token and len(access_token) > 10 else f"Access Token: {access_token}")
    print()
    
    if not merchant_id or not access_token:
        print("❌ ERROR: Missing Clover credentials in .env file")
        print("Please set CLOVER_MERCHANT_ID and CLOVER_ACCESS_TOKEN")
        return False
    
    if access_token == 'your_actual_clover_access_token_here':
        print("❌ ERROR: Access token is still the placeholder value")
        print("Please replace 'your_actual_clover_access_token_here' with your real access token")
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
            print("Please check your access token in the .env file")
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
    else:
        print("\n💡 To fix this:")
        print("1. Get your access token from Clover Developer Dashboard")
        print("2. Update the .env file with your real access token")
        print("3. Restart the backend server") 