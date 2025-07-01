import requests
import datetime
import time

# CONFIGURE THESE
API_URL = "https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com/api/clover/sync/sales"
API_KEY = "supersecretkey1234567890"  # Change if you set a custom key in Heroku

# Set your date range - just the last 3 days to test
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=3)

print(f"Syncing sales from {start_date} to {end_date}")

# Loop through each day
current = start_date
while current <= end_date:
    next_day = current + datetime.timedelta(days=1)
    payload = {
        "start_date": current.isoformat() + "T00:00:00Z",
        "end_date": current.isoformat() + "T23:59:59Z"
    }
    print(f"Syncing sales for {current}...")
    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": API_KEY
        }
        resp = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=60  # Reduced timeout
        )
        if resp.status_code == 200:
            print(f"✅ Success: {resp.status_code}")
        else:
            print(f"❌ Error: {resp.status_code}, Response: {resp.text[:200]}...")
    except Exception as e:
        print(f"❌ Error syncing {current}: {e}")
    
    # Wait longer to avoid rate limits
    print("Waiting 10 seconds before next request...")
    time.sleep(10)
    current = next_day

print("Done!") 