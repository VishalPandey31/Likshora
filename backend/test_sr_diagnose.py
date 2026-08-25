from app import create_app
from app.services.shiprocket_service import ShiprocketService
import requests

app = create_app()
with app.app_context():
    headers = ShiprocketService._headers()
    base_url = ShiprocketService._get_base_url()

    print("--- 1. Fetching Orders ---")
    res_orders = requests.get(f"{base_url}/orders", headers=headers)
    print("Orders Status:", res_orders.status_code)
    try:
        print("Orders Sample:", res_orders.json().get("data", [])[:2])
    except Exception as e:
        print("Orders Error:", e, res_orders.text)
