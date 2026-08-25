import requests
import json

url = "https://likshora-api.onrender.com/api/v1/auth/login"
payload = {
    "email": "karanrajput.officials@gmail.com",
    "password": "Karan@2026"
}
headers = {"Content-Type": "application/json"}

try:
    print("Connecting to live production API...")
    res = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {res.status_code}")
    print(json.dumps(res.json(), indent=2))
except Exception as e:
    print(f"Internal error test: {e}")
