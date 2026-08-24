import json
import pytest
from datetime import datetime, timezone
from app.models import Order, OrderItem, Address, Product, Category, User, Payment, Shipment, ShipmentTrackingEvent
from app.services import TrackingService, normalize_shiprocket_status
from app.extensions import db


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-track-customer-a-uid",
            name="Track Customer A",
            email="track_a@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def customer_user_b(app):
    with app.app_context():
        user = User(
            supabase_uid="test-track-customer-b-uid",
            name="Track Customer B",
            email="track_b@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User(
            supabase_uid="test-track-admin-uid",
            name="Track Admin",
            email="track_admin@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def tracking_setup(app, customer_user_a):
    with app.app_context():
        cat = Category(name="Jackets", slug="jackets", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p1 = Product(
            category_id=cat.id,
            name="Denim Jacket",
            slug="denim-jacket",
            sku="JKT-DEN-01",
            price=2500.00,
            stock_quantity=15,
            is_active=True,
        )
        db.session.add(p1)
        db.session.commit()

        addr_a = Address(
            user_id=customer_user_a["id"],
            full_name="Track Customer A",
            phone="9876543210",
            address_line1="500 Track Boulevard",
            city="Pune",
            state="Maharashtra",
            postal_code="411001",
            country="India",
            is_default=True,
        )
        db.session.add(addr_a)
        db.session.commit()

        # 1. Order Placed / Confirmed Order
        o_confirmed = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-TRK-CONF-01",
            subtotal=2500.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=2500.00,
            payment_method="online",
            payment_status="paid",
            order_status="confirmed",
            shipping_full_name=addr_a.full_name,
            shipping_phone=addr_a.phone,
            shipping_address_line1=addr_a.address_line1,
            shipping_city=addr_a.city,
            shipping_state=addr_a.state,
            shipping_postal_code=addr_a.postal_code,
            shipping_country=addr_a.country,
        )
        # 2. Shipped Order with Shipment
        o_shipped = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-TRK-SHIP-02",
            subtotal=2500.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=2500.00,
            payment_method="cod",
            payment_status="pending",
            order_status="shipped",
            shipping_full_name=addr_a.full_name,
            shipping_phone=addr_a.phone,
            shipping_address_line1=addr_a.address_line1,
            shipping_city=addr_a.city,
            shipping_state=addr_a.state,
            shipping_postal_code=addr_a.postal_code,
            shipping_country=addr_a.country,
        )
        # 3. Cancelled Order
        o_cancelled = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-TRK-CANCEL-03",
            subtotal=2500.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=2500.00,
            payment_method="online",
            payment_status="pending",
            order_status="cancelled",
            shipping_full_name=addr_a.full_name,
            shipping_phone=addr_a.phone,
            shipping_address_line1=addr_a.address_line1,
            shipping_city=addr_a.city,
            shipping_state=addr_a.state,
            shipping_postal_code=addr_a.postal_code,
            shipping_country=addr_a.country,
        )
        db.session.add_all([o_confirmed, o_shipped, o_cancelled])
        db.session.commit()

        # Add Order items
        item1 = OrderItem(order_id=o_confirmed.id, product_id=p1.id, product_name=p1.name, sku=p1.sku, quantity=1, unit_price=p1.price, subtotal=2500.00)
        item2 = OrderItem(order_id=o_shipped.id, product_id=p1.id, product_name=p1.name, sku=p1.sku, quantity=1, unit_price=p1.price, subtotal=2500.00)
        item3 = OrderItem(order_id=o_cancelled.id, product_id=p1.id, product_name=p1.name, sku=p1.sku, quantity=1, unit_price=p1.price, subtotal=2500.00)
        db.session.add_all([item1, item2, item3])

        # Add Shipment for Shipped Order
        shipment = Shipment(
            order_id=o_shipped.id,
            provider="shiprocket",
            shipment_id="SR-TRK-88801",
            awb_code="AWB-TRK-99901",
            courier_name="Delhivery Express",
            tracking_url="https://shiprocket.co/tracking/AWB-TRK-99901",
            status="in_transit",
            shipped_at=datetime.now(timezone.utc),
        )
        db.session.add(shipment)
        db.session.commit()

        return {
            "order_confirmed_id": o_confirmed.id,
            "order_shipped_id": o_shipped.id,
            "order_cancelled_id": o_cancelled.id,
            "shipment_id": shipment.id,
        }


# -----------------------------------------------------------------------------
# PHASE 14 ORDER TRACKING TEST SUITE
# -----------------------------------------------------------------------------

def test_status_normalization_layer():
    """Test raw Shiprocket statuses normalize to internal status enum."""
    assert normalize_shiprocket_status("NEW") == "confirmed"
    assert normalize_shiprocket_status("READY TO SHIP") == "processing"
    assert normalize_shiprocket_status("PICKED UP") == "picked_up"
    assert normalize_shiprocket_status("IN TRANSIT") == "in_transit"
    assert normalize_shiprocket_status("OUT FOR DELIVERY") == "out_for_delivery"
    assert normalize_shiprocket_status("DELIVERED") == "delivered"
    assert normalize_shiprocket_status("CANCELLED") == "cancelled"
    assert normalize_shiprocket_status("RTO IN TRANSIT") == "returned"


def test_customer_access_own_order_tracking_success(client, customer_user_a, tracking_setup, monkeypatch):
    """Test customer accesses their own order tracking (200 OK & clean contract)."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    o_id = tracking_setup["order_shipped_id"]

    response = client.get(f"/api/v1/orders/{o_id}/tracking", headers={"Authorization": "Bearer token-a"})
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["order_id"] == o_id
    assert data["order_status"] == "shipped"
    assert data["payment_method"] == "cod"
    assert data["shipment"]["awb_code"] == "AWB-TRK-99901"
    assert data["shipment"]["tracking_url"] is not None

    timeline = data["timeline"]
    assert len(timeline) == 6

    # Verify timeline flags and stages
    shipped_step = next(s for s in timeline if s["status"] == "shipped")
    assert shipped_step["completed"] is True
    assert shipped_step["current"] is True
    assert shipped_step["timestamp"] is not None

    delivered_step = next(s for s in timeline if s["status"] == "delivered")
    assert delivered_step["completed"] is False
    assert delivered_step["current"] is False
    assert delivered_step["timestamp"] is None


def test_customer_idor_protection_other_user_tracking_denied(client, customer_user_b, tracking_setup, monkeypatch):
    """Test customer attempting to access another user's tracking returns 404 (IDOR protected)."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_b["supabase_uid"], "email": customer_user_b["email"]},
    )
    o_id = tracking_setup["order_shipped_id"]

    response = client.get(f"/api/v1/orders/{o_id}/tracking", headers={"Authorization": "Bearer token-b"})
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "ORDER_NOT_FOUND"


def test_admin_access_any_order_tracking(client, admin_user, tracking_setup, monkeypatch):
    """Test Admin can access tracking for any order (200 OK)."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    o_id = tracking_setup["order_shipped_id"]

    response = client.get(f"/api/v1/orders/{o_id}/tracking", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 200
    assert response.get_json()["data"]["order_id"] == o_id


def test_cancelled_order_tracking_timeline(client, customer_user_a, tracking_setup, monkeypatch):
    """Test tracking for cancelled order displays cancelled timeline state without marking delivered."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    o_id = tracking_setup["order_cancelled_id"]

    response = client.get(f"/api/v1/orders/{o_id}/tracking", headers={"Authorization": "Bearer token-a"})
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["order_status"] == "cancelled"
    timeline = data["timeline"]
    cancel_step = next(s for s in timeline if s["status"] == "cancelled")
    assert cancel_step["completed"] is True
    assert cancel_step["current"] is True

    delivered_step = next(s for s in timeline if s["status"] == "delivered")
    assert delivered_step["completed"] is False


def test_admin_manual_tracking_sync_refresh(client, admin_user, tracking_setup, monkeypatch):
    """Test Admin manual tracking refresh POST /api/v1/shipments/<id>/tracking/sync."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    s_id = tracking_setup["shipment_id"]

    response = client.post(f"/api/v1/shipments/{s_id}/tracking/sync", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert response.get_json()["data"]["shipment"]["awb_code"] == "AWB-TRK-99901"


def test_webhook_logs_historical_tracking_events(client, app, admin_user, tracking_setup, monkeypatch):
    """Test Shiprocket webhook logs historical tracking events into shipment_tracking_events table."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    s_id = tracking_setup["shipment_id"]
    token = app.config["SHIPROCKET_WEBHOOK_TOKEN"]

    # Post OUT FOR DELIVERY webhook
    payload_ofd = {
        "event_id": "evt_hist_ofd_001",
        "current_status": "OUT FOR DELIVERY",
        "awb": "AWB-TRK-99901",
        "location": "Pune West",
        "activity": "Out for delivery with rider",
    }
    res_wh = client.post(
        "/api/v1/shipments/shiprocket/webhook",
        data=json.dumps(payload_ofd),
        content_type="application/json",
        headers={"X-Api-Key": token},
    )
    assert res_wh.status_code == 200

    with app.app_context():
        events = ShipmentTrackingEvent.query.filter_by(shipment_id=s_id).all()
        assert len(events) >= 1
        ofd_evt = next(e for e in events if e.status == "out_for_delivery")
        assert ofd_evt.external_status == "OUT FOR DELIVERY"
        assert ofd_evt.location == "Pune West"


def test_no_fabricated_timestamps_rule(client, customer_user_a, tracking_setup, monkeypatch):
    """Test uncompleted timeline stages have null timestamps without date fabrication."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    o_id = tracking_setup["order_confirmed_id"]

    response = client.get(f"/api/v1/orders/{o_id}/tracking", headers={"Authorization": "Bearer token-a"})
    assert response.status_code == 200
    timeline = response.get_json()["data"]["timeline"]

    for step in timeline:
        if not step["completed"]:
            assert step["timestamp"] is None


def test_cod_payment_remains_pending_during_transit(client, app, tracking_setup):
    """Test COD payment_status remains 'pending' while shipment is in transit."""
    with app.app_context():
        order = db.session.get(Order, tracking_setup["order_shipped_id"])
        assert order.payment_method == "cod"
        assert order.payment_status == "pending"
        assert order.order_status == "shipped"
