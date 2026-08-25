from app import create_app
from app.extensions import db
from app.models import Order
from app.services.shiprocket_service import ShiprocketService
import requests

app = create_app()

with app.app_context():
    order = Order.query.order_by(Order.id.desc()).first()
    print(f"Testing Shiprocket for Order #{order.id}...")
    
    # Calculate weight
    total_weight = 0.5
    
    sr_items = [
        {
            "name": item.product_name,
            "sku": item.sku or f"SKU-{item.product_id or item.id}",
            "units": item.quantity,
            "selling_price": float(item.unit_price),
            "discount": 0,
            "tax": 0,
        }
        for item in order.order_items
    ]

    customer_email = order.user.email if order.user else "test@example.com"

    sr_payload = {
        "order_id": order.order_number,
        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "2026-08-26 10:00",
        "pickup_location": app.config.get("SHIPROCKET_PICKUP_LOCATION", "Primary"),
        "billing_customer_name": order.shipping_full_name or "Customer",
        "billing_last_name": "",
        "billing_address": order.shipping_address_line1 or "Address test",
        "billing_address_2": order.shipping_address_line2 or "",
        "billing_city": order.shipping_city or "BLR",
        "billing_pincode": order.shipping_postal_code or "560001",
        "billing_state": order.shipping_state or "KA",
        "billing_country": order.shipping_country or "India",
        "billing_email": customer_email,
        "billing_phone": order.shipping_phone or "9999999999",
        "billing_is_shipping": True,
        "order_items": sr_items,
        "payment_method": "COD" if order.payment_method == "cod" else "Prepaid",
        "shipping_charges": float(order.shipping_amount),
        "discount": float(order.discount_amount),
        "sub_total": float(order.subtotal),
        "length": 10,
        "breadth": 10,
        "height": 10,
        "weight": total_weight,
    }

    url = f"{ShiprocketService._get_base_url()}/orders/create/adhoc"
    headers = ShiprocketService._headers()

    print("\n--- Sending Payload ---")
    res = requests.post(url, json=sr_payload, headers=headers)
    print("STATUS:", res.status_code)
    try:
        print("JSON:", res.json())
    except:
        print("TEXT:", res.text)
