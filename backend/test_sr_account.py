from app import create_app
from app.services.shiprocket_service import ShiprocketService
import requests

app = create_app()
with app.app_context():
    url = f"{ShiprocketService._get_base_url()}/account/details"
    headers = ShiprocketService._headers()
    response = requests.get(url, headers=headers)
    print("STATUS:", response.status_code)
    try:
        print("BODY:", response.json())
    except:
        print("BODY:", response.text)
