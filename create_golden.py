import os
import requests
import json
import urllib.request
from io import BytesIO
import base64
from PIL import Image

def download_image(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return response.read()

os.makedirs('backend/tests/golden_case', exist_ok=True)

print("Downloading image...")
img_bytes = download_image("https://upload.wikimedia.org/wikipedia/commons/8/89/Tomato_je.jpg")
try:
    img = Image.open(BytesIO(img_bytes))
    out_bytes = BytesIO()
    img.convert('RGB').save(out_bytes, format='JPEG')
    img_bytes = out_bytes.getvalue()
except Exception:
    pass

with open('backend/tests/golden_case/tomato.jpg', 'wb') as f:
    f.write(img_bytes)

img_b64 = base64.b64encode(img_bytes).decode('utf-8')
data_url = f"data:image/jpeg;base64,{img_b64}"

url_scan = "http://localhost:8000/scan-produce"
payload = {
    "produce_type": "tomato",
    "image": data_url
}

print("Running POST /scan-produce...")
res_scan = requests.post(url_scan, json=payload)

with open('backend/tests/golden_case/golden_response.json', 'w') as f:
    json.dump(res_scan.json(), f, indent=2)

print("Golden response saved.")
