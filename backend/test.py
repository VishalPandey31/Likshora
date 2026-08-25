from app import create_app
from app.extensions import db
from app.models import Order, Payment, Shipment

app = create_app()
with app.app_context():
    print("Latest Orders:")
    for o in Order.query.order_by(Order.created_at.desc()).limit(3).all():
        print(f"[{o.id}] {o.order_number} - {o.order_status} - {o.payment_method}")
        for s in o.shipments:
            print(f"  Shipment: {s.id} - {s.status} - ER: {s.error_message}")
        print("  Payments:")
        for p in o.payments:
            print(f"    [{p.id}] Status: {p.status} - Total: {p.amount}")
