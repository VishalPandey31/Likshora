from app import create_app
from app.services.shiprocket_service import ShiprocketService
import requests

app = create_app()
with app.app_context():
    headers = ShiprocketService._headers()
    base_url = ShiprocketService._get_base_url()

    sr_payload = {
        "order_id": "ORD-TEST-COD-1339",
        "order_date": "2026-08-26 10:00",
        "channel_id": "11942976", # Custom channel
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
        "order_items": [{"name": "Maroon Kurti", "sku": "SKU-1", "units": 1, "selling_price": 100.0, "discount": 0, "tax": 0}],
        "payment_method": "COD",
        "shipping_charges": 0,
        "discount": 0,
        "sub_total": 100.0,
        "length": 10,
        "breadth": 10,
        "height": 10,
        "weight": 0.5,
    }
    
    url = f"{base_url}/orders/create/custom"
    response = requests.post(url, json=sr_payload, headers=headers)
    print("\n\n--- CUSTOM ORDER TEST ---")
    print("STATUS:", response.status_code)
    try:
        print("BODY:", response.json())
    except:
        print("BODY:", response.text)
