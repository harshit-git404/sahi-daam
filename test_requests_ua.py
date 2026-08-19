import requests
import time

url = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
params = {
    "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b",
    "format": "json",
    "limit": 5
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

start = time.time()
print("Starting requests.get with custom headers...")
try:
    resp = requests.get(url, params=params, headers=headers, verify=False, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Time: {time.time() - start:.2f}s")
    print(f"Records: {len(resp.json().get('records', []))}")
except Exception as e:
    print(f"Error: {e}")
