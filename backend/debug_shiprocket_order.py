from app import create_app
from app.services.shiprocket_service import ShiprocketService
from datetime import datetime, timezone

app = create_app()

with app.app_context():
    order_id_test = f"TEST-ORDER-{int(datetime.now().timestamp())}"
    
    sr_payload = {
        "order_id": order_id_test,
        "order_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "pickup_location": app.config.get("SHIPROCKET_PICKUP_LOCATION", "Primary"),
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
            {
                "name": "Test Product",
                "sku": "SKU-999",
                "units": 1,
                "selling_price": 100.0,
                "discount": 0,
                "tax": 0,
            }
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

    try:
        print(f"Attempting to create order {order_id_test} in Shiprocket...")
        res = ShiprocketService.create_order(sr_payload)
        print("✅ SUCCESS!")
        print(res)
    except Exception as e:
        print("❌ SHIPROCKET API ERROR:")
        print(e)
