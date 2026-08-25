import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.environ.get("SHIPROCKET_EMAIL")
PASSWORD = os.environ.get("SHIPROCKET_PASSWORD")
BASE_URL = "https://apiv2.shiprocket.in/v1/external"

print(f"Authenticating as {EMAIL}...")
res_auth = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})

if res_auth.status_code != 200:
    print("Auth Failed:", res_auth.status_code, res_auth.text)
    exit(1)

token = res_auth.json().get("token")
print("Auth Success, Token obtained.")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("\n--- 1. Fetching Pickup Locations ---")
res_pick = requests.get(f"{BASE_URL}/settings/company/pickup", headers=headers)
print("Status:", res_pick.status_code)
try:
    print(res_pick.json())
except:
    print(res_pick.text)

print("\n--- 2. Fetching Serviceability (Testing basic GET access) ---")
res_serv = requests.get(f"{BASE_URL}/courier/serviceability/", params={
    "pickup_postcode": 110001,
    "delivery_postcode": 560001,
    "weight": 0.5,
    "cod": 1
}, headers=headers)
print("Status:", res_serv.status_code)

print("\n--- 3. Creating Test Order (COD) ---")
sr_payload = {
    "order_id": f"ORD-TEST-{int(time.time())}",
    "order_date": "2026-08-26 10:00",
    "pickup_location": "Primary",
    "billing_customer_name": "Test User",
    "billing_last_name": "",
    "billing_address": "45 Tech Park",
    "billing_address_2": "",
    "billing_city": "Bengaluru",
    "billing_pincode": "560001",
    "billing_state": "Karnataka",
    "billing_country": "India",
    "billing_email": "test@example.com",
    "billing_phone": "9988776655",
    "billing_is_shipping": True,
    "order_items": [{"name": "Kurti", "sku": "KU-1", "units": 1, "selling_price": 500.0, "discount": 0, "tax": 0}],
    "payment_method": "COD",
    "shipping_charges": 0,
    "discount": 0,
    "sub_total": 500.0,
    "length": 10,
    "breadth": 10,
    "height": 10,
    "weight": 0.5,
}

res_order = requests.post(f"{BASE_URL}/orders/create/adhoc", json=sr_payload, headers=headers)
print("Status:", res_order.status_code)
try:
    print(res_order.json())
except:
    print(res_order.text)

print("\n--- 4. Checking Company Details ---")
res_comp = requests.get(f"{BASE_URL}/settings/company/export", headers=headers)
print("Status:", res_comp.status_code)

print("Done.")
