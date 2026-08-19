import requests
import time

url = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
params = {
    "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b",
    "format": "json",
    "limit": 5
}

start = time.time()
print("Starting requests.get...")
try:
    resp = requests.get(url, params=params, verify=False, timeout=20)
    print(f"Status: {resp.status_code}")
    print(f"Time: {time.time() - start:.2f}s")
    print(f"Records: {len(resp.json().get('records', []))}")
except Exception as e:
    print(f"Error: {e}")
