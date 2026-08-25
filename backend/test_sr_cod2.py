from app import create_app
from app.services.shiprocket_service import ShiprocketService
import requests

app = create_app()
with app.app_context():
    sr_payload = {
        "order_id": "ORD-TEST-COD-303",
        "order_date": "2026-08-26 10:00",
        "pickup_location": "Primary",
        "billing_customer_name": "Test User",
        "billing_last_name": "Test",
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
    
    url = f"{ShiprocketService._get_base_url()}/orders/create/adhoc"
    headers = ShiprocketService._headers()
    response = requests.post(url, json=sr_payload, headers=headers)
    print("STATUS:", response.status_code)
    try:
        print("BODY:", response.json())
    except:
        print("BODY:", response.text)
