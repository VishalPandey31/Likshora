from app import create_app
from app.services.shiprocket_service import ShiprocketService
import requests

app = create_app()
with app.app_context():
    headers = ShiprocketService._headers()
    base_url = ShiprocketService._get_base_url()

    print("--- 1. Fetching Channels ---")
    res_ch = requests.get(f"{base_url}/channels", headers=headers)
    print("Channels Status:", res_ch.status_code)
    try:
        channels_data = res_ch.json()
        print("Channels returned:")
        for ch in channels_data.get('data', []):
            print(f" -> ID: {ch.get('id')}, Name: {ch.get('name')}, Source: {ch.get('base_channel_code')}")
    except Exception as e:
        print("Channels Error:", e)

    print("\n--- 2. Fetching Company Details ---")
    res_comp = requests.get(f"{base_url}/settings/company/export", headers=headers)
    print("Company Status:", res_comp.status_code)
    try:
        print(res_comp.json())
    except:
        pass

