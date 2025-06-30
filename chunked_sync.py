import requests
import datetime
import time

# CONFIGURE THESE
API_URL = "https://plateiq-analytics-api-f6a987ab13c5.herokuapp.com/api/clover/sync/sales"
# If your endpoint requires authentication, set your session cookie here:
ADMIN_COOKIE = None  # e.g., 'your_session_cookie_here'

# Set your date range (YYYY, M, D)
start_date = datetime.date(2025, 6, 1)
end_date = datetime.date(2025, 6, 30)

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
        headers = {"Content-Type": "application/json"}
        if ADMIN_COOKIE:
            headers["Cookie"] = f"plateiq_session={ADMIN_COOKIE}"
        resp = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=120
        )
        print(f"Status: {resp.status_code}, Response: {resp.text}")
    except Exception as e:
        print(f"Error syncing {current}: {e}")
    # Wait to avoid rate limits
    time.sleep(5)
    current = next_day

print("Done!") 