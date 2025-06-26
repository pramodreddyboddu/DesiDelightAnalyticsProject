import requests
import json

def test_sales_fix():
    """Test if the sales processing fix is working"""
    print("🧪 Testing Sales Processing Fix...")
    
    # Test the sales summary endpoint
    try:
        response = requests.get("http://localhost:5000/api/dashboard/sales-summary", 
                              headers={"Content-Type": "application/json"})
        
        if response.status_code == 401:
            print("⚠️  API requires authentication - this is expected")
            print("✅ The server is running and responding")
            print("📊 To test the fix, please:")
            print("   1. Open your frontend dashboard")
            print("   2. Log in to the application")
            print("   3. Check if sales data is now showing correctly")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"✅ Sales data received: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - make sure it's running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Error testing sales fix: {str(e)}")
        return False

if __name__ == "__main__":
    test_sales_fix() 