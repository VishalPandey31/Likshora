from app import create_app
from app.extensions import db
from app.models import Order, Shipment

app = create_app()
with app.app_context():
    print("Fetching latest order...")
    latest_order = Order.query.order_by(Order.id.desc()).first()
    
    if latest_order:
        print(f"Order #{latest_order.id}, Num: {latest_order.order_number}, Status: {latest_order.order_status}, Payment: {latest_order.payment_method}")
        
        shipments = Shipment.query.filter_by(order_id=latest_order.id).all()
        print(f"Found {len(shipments)} shipments for this order:")
        for s in shipments:
            print(f" -> ID: {s.id}, Provider: {s.provider}, Status: {s.status}")
            if s.error_message:
                print(f"    ERROR: {s.error_message}")
    else:
        print("No orders found.")
