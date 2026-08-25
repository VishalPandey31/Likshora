import requests

email = "karanraj7769958707@gmail.com"
password = "sVim8OiyzbXGRF$g8L*6d8FbE3o!9IFR"

# Login
login_res = requests.post("https://apiv2.shiprocket.in/v1/external/auth/login", json={"email": email, "password": password})
token = login_res.json().get("token")

# Create Order
sr_payload = {
    "order_id": "TEST-ORDER-12345",
    "order_date": "2026-08-25 12:00",
    "pickup_location": "Primary",
    "billing_customer_name": "Test User",
    "billing_last_name": "Smith",
    "billing_address": "House 123, Sector 45, ABC Colony",
    "billing_address_2": "",
    "billing_city": "Gurugram",
    "billing_pincode": "122002",
    "billing_state": "Haryana",
    "billing_country": "India",
    "billing_email": "test@example.com",
    "billing_phone": "9876543210",
    "shipping_is_billing": True,
    "order_items": [
        {"name": "Test Product", "sku": "SKU-999", "units": 1, "selling_price": 100.0, "discount": 0, "tax": 0}
    ],
    "payment_method": "Prepaid",
    "shipping_charges": 0,
    "discount": 0,
    "sub_total": 100.0,
    "length": 10,
    "breadth": 10,
    "height": 10,
    "weight": 0.5,
}

res = requests.post(
    "https://apiv2.shiprocket.in/v1/external/orders/create/adhoc",
    json=sr_payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
)
print("STATUS:", res.status_code)
print("BODY:", res.text)
