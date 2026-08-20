import requests
import json
import os

# Test data.gov.in API
url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
params = {
    "api-key": os.getenv("DATA_GOV_API_KEY", ""),
    "format": "json",
    "limit": 10
}
try:
    response = requests.get(url, params=params)
    print("data.gov.in Status:", response.status_code)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2)[:500])
except Exception as e:
    print("data.gov.in Error:", e)

