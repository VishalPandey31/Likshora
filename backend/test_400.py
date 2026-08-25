import requests

PROD_URL = "https://likshora-api.onrender.com/api/v1"

print("--- Logging in to Prod ---")
res_auth = requests.post(f"{PROD_URL}/auth/login", json={
    "email": "customer@example.com",
    "password": "password123"
})
if res_auth.status_code != 200:
    print("Failed to login to prod for test", res_auth.text)
    token = None
else:
    token = res_auth.json()["access_token"]
    print("Token obtained")

if token:
    print("\n--- Sending Order ---")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "payment_method": "cod",
        "shipping_address": {
            "recipient": "Customer",
            "street": "123 Test",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
            "phone": "9988776655"
        },
        "items": [
            {
                "product_id": "AK02",
                "quantity": 1,
                "size": "M"
            }
        ]
    }
    res_order = requests.post(f"{PROD_URL}/orders", json=payload, headers=headers)
    print("STATUS:", res_order.status_code)
    print("BODY:", res_order.text)
