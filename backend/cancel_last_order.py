from app import create_app
from app.extensions import db
from app.models import Order, Shipment
from app.services.shiprocket_service import ShiprocketService

app = create_app()
with app.app_context():
    print("Fetching the latest successfully synced shipment...")
    # Get latest order and shipment
    shipment = Shipment.query.filter(Shipment.shiprocket_order_id != None).order_by(Shipment.id.desc()).first()
    
    if shipment and shipment.shiprocket_order_id:
        print(f"Canceling Shiprocket Order ID: {shipment.shiprocket_order_id}")
        try:
            res = ShiprocketService.cancel_order([int(shipment.shiprocket_order_id)])
            print("Cancellation Success! JSON:", res)
            shipment.status = "cancelled"
            db.session.commit()
            print("Refunded wallet. Database status updated to cancelled.")
        except Exception as e:
            print("Error canceling:", str(e))
    else:
        print("No active Shiprocket shipment found.")
