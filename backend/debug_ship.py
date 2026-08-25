from app import create_app
from app.services.shiprocket_service import ShiprocketService

app = create_app()

with app.app_context():
    try:
        token = ShiprocketService.get_auth_token(force_refresh=True)
        print("✅ Shiprocket Auth SUCCESS!")
        print(f"Token (First 20 chars): {token[:20]}...")
        
        # Test a generic lookup to verify full access
        res = ShiprocketService.get_courier_serviceability("110001", "122002", 0.5)
        print("✅ Shiprocket Serviceability API SUCCESS!")
        print(f"Available Couriers: {len(res.get('data', {}).get('available_courier_companies', []))}")
        
    except Exception as e:
        print("❌ ERROR OCCURRED:")
        print(e)
