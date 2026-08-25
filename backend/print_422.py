import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://apiv2.shiprocket.in/v1/external"
res_auth = requests.post(f"{BASE_URL}/auth/login", json={"email": os.environ.get("SHIPROCKET_EMAIL"), "password": os.environ.get("SHIPROCKET_PASSWORD")})
token = res_auth.json().get("token")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

sr_payload = {
    "order_id": "ORD-TEST-998-VAL",
    "order_date": "2026-08-26 10:00",
    "pickup_location": os.environ.get("SHIPROCKET_PICKUP_LOCATION", "Primary"),
    "billing_customer_name": "Customer",
    "billing_last_name": "",
    "billing_address": "Flat 402, Lotus Apartments, MG Road",
    "billing_address_2": "",
    "billing_city": "Bengaluru",
    "billing_pincode": "560001",
    "billing_state": "Karnataka",
    "billing_country": "India",
    "billing_email": "customer@example.com",
    "billing_phone": "9876543210",
    "billing_is_shipping": True,
    "order_items": [
        {
            "name": "Rust Bell-Sleeve Printed Kurti",
            "sku": "AK01-RUST",
            "units": 1,
            "selling_price": 2299.0,
            "discount": 0,
            "tax": 0
        }
    ],
    "payment_method": "COD",
    "shipping_charges": 0.0,
    "discount": 0.0,
    "sub_total": 2299.0,
    "length": 10,
    "breadth": 10,
    "height": 10,
    "weight": 0.5
}

res = requests.post(f"{BASE_URL}/orders/create/adhoc", json=sr_payload, headers=headers)
with open("shiprocket_err.txt", "w") as f:
    f.write(str(res.json()))
