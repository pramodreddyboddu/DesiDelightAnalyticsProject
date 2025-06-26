#!/usr/bin/env python3
"""
Script to help find your Clover merchant ID
"""
import requests

def find_merchant_info(access_token):
    """Try to find merchant information with the access token"""
    print("=== Finding Your Clover Merchant Information ===")
    print(f"Access Token: {access_token[:10]}..." if access_token and len(access_token) > 10 else f"Access Token: {access_token}")
    print()
    
    # Try to get merchant info without specifying merchant ID
    url = "https://api.clover.com/v3/merchants"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("Searching for your merchant information...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Found your merchant information!")
            print()
            
            if 'elements' in data and data['elements']:
                for merchant in data['elements']:
                    print(f"Merchant ID: {merchant.get('id', 'N/A')}")
                    print(f"Name: {merchant.get('name', 'N/A')}")
                    print(f"Address: {merchant.get('address', {}).get('address1', 'N/A')}")
                    print(f"Phone: {merchant.get('phone', 'N/A')}")
                    print(f"Website: {merchant.get('website', 'N/A')}")
                    print("-" * 50)
            else:
                print("No merchants found for this access token.")
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            print()
            print("This could mean:")
            print("1. The access token is invalid or expired")
            print("2. The access token doesn't have the right permissions")
            print("3. You need to create a new app in Clover Developer Dashboard")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        print()
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    # Replace this with your actual access token
    access_token = "e6e48423-d223-f206-0ab2-572cce38bff4"
    
    if access_token == "YOUR_ACCESS_TOKEN_HERE":
        print("❌ Please replace 'YOUR_ACCESS_TOKEN_HERE' with your actual access token")
        print("Then run this script again.")
    else:
        find_merchant_info(access_token) 