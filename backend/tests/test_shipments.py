import json
import pytest
from app.models import Order, OrderItem, Address, Product, Category, User, Payment, Shipment, ShipmentWebhookEvent
from app.extensions import db
from app.services import ShiprocketService


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-ship-a-uid",
            name="Ship Customer A",
            email="ship_a@example.com",
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
            supabase_uid="test-customer-ship-b-uid",
            name="Ship Customer B",
            email="ship_b@example.com",
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
            supabase_uid="test-admin-ship-uid",
            name="Admin Shipper",
            email="adminship@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def shipment_setup(app, customer_user_a):
    with app.app_context():
        cat = Category(name="Apparel", slug="apparel", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p1 = Product(
            category_id=cat.id,
            name="Cotton T-Shirt",
            slug="cotton-t-shirt",
            sku="TSH-COT-01",
            price=1200.00,
            stock_quantity=20,
            is_active=True,
        )
        db.session.add(p1)
        db.session.commit()

        addr_a = Address(
            user_id=customer_user_a["id"],
            full_name="Ship Customer A",
            phone="9876543210",
            address_line1="100 Express Way",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400001",
            country="India",
            is_default=True,
        )
        db.session.add(addr_a)
        db.session.commit()

        # Paid Online Order
        order_paid = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-SHIP-PAID-01",
            subtotal=1200.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1200.00,
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
        # Unpaid Online Order
        order_unpaid = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-SHIP-UNPAID-02",
            subtotal=1200.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1200.00,
            payment_method="online",
            payment_status="pending",
            order_status="pending",
            shipping_full_name=addr_a.full_name,
            shipping_phone=addr_a.phone,
            shipping_address_line1=addr_a.address_line1,
            shipping_city=addr_a.city,
            shipping_state=addr_a.state,
            shipping_postal_code=addr_a.postal_code,
            shipping_country=addr_a.country,
        )
        # Pending COD Order
        order_cod = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-SHIP-COD-03",
            subtotal=2400.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=2400.00,
            payment_method="cod",
            payment_status="pending",
            order_status="pending",
            shipping_full_name=addr_a.full_name,
            shipping_phone=addr_a.phone,
            shipping_address_line1=addr_a.address_line1,
            shipping_city=addr_a.city,
            shipping_state=addr_a.state,
            shipping_postal_code=addr_a.postal_code,
            shipping_country=addr_a.country,
        )
        # Cancelled Order
        order_cancelled = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-SHIP-CANCEL-04",
            subtotal=1200.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1200.00,
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
        db.session.add_all([order_paid, order_unpaid, order_cod, order_cancelled])
        db.session.commit()

        # Add Order Items
        item1 = OrderItem(order_id=order_paid.id, product_id=p1.id, product_name=p1.name, sku=p1.sku, quantity=1, unit_price=p1.price, subtotal=p1.price)
        item2 = OrderItem(order_id=order_unpaid.id, product_id=p1.id, product_name=p1.name, sku=p1.sku, quantity=1, unit_price=p1.price, subtotal=p1.price)
        item3 = OrderItem(order_id=order_cod.id, product_id=p1.id, product_name=p1.name, sku=p1.sku, quantity=2, unit_price=p1.price, subtotal=2400.00)
        item4 = OrderItem(order_id=order_cancelled.id, product_id=p1.id, product_name=p1.name, sku=p1.sku, quantity=1, unit_price=p1.price, subtotal=p1.price)
        db.session.add_all([item1, item2, item3, item4])

        # Add payment records
        pay_cod = Payment(order_id=order_cod.id, payment_method="cod", provider="cod", amount=2400.00, status="pending")
        pay_paid = Payment(order_id=order_paid.id, payment_method="online", provider="razorpay", amount=1200.00, status="captured")
        db.session.add_all([pay_cod, pay_paid])
        db.session.commit()

        return {
            "order_paid_id": order_paid.id,
            "order_unpaid_id": order_unpaid.id,
            "order_cod_id": order_cod.id,
            "order_cancelled_id": order_cancelled.id,
        }


# -----------------------------------------------------------------------------
# SHIPROCKET TEST SUITE
# -----------------------------------------------------------------------------

def test_shiprocket_authentication_service(app):
    """Test ShiprocketService token authentication and caching."""
    with app.app_context():
        token = ShiprocketService.get_auth_token()
        assert token is not None
        assert len(token) > 0


def test_admin_create_shipment_prepaid_success(client, app, admin_user, shipment_setup, monkeypatch):
    """Test Admin creates shipment for paid prepaid order -> 201 Created with assigned status and AWB."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    o_id = shipment_setup["order_paid_id"]

    response = client.post("/api/v1/shipments/create", json={"order_id": o_id}, headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 201
    data = response.get_json()["data"]

    assert data["order_id"] == o_id
    assert data["status"] == "assigned"
    assert data["awb_code"].startswith("AWB-SR-")
    assert data["courier_name"] is not None

    with app.app_context():
        order = db.session.get(Order, o_id)
        assert order.order_status in ["confirmed", "processing"]


def test_admin_create_shipment_cod_success(client, app, admin_user, shipment_setup, monkeypatch):
    """Test Admin creates shipment for confirmed COD order -> 201 Created."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    o_id = shipment_setup["order_cod_id"]

    response = client.post("/api/v1/shipments/create", json={"order_id": o_id}, headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 201
    data = response.get_json()["data"]

    assert data["status"] == "assigned"
    assert data["awb_code"] is not None


def test_create_shipment_validation_errors(client, admin_user, shipment_setup, monkeypatch):
    """Test cancelled order or unpaid online order rejected for shipment creation."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    # Unpaid online order -> 400
    res_unpaid = client.post("/api/v1/shipments/create", json={"order_id": shipment_setup["order_unpaid_id"]}, headers={"Authorization": "Bearer admin-token"})
    assert res_unpaid.status_code == 400
    assert res_unpaid.get_json()["error"]["code"] == "UNPAID_ORDER"

    # Cancelled order -> 400
    res_cancel = client.post("/api/v1/shipments/create", json={"order_id": shipment_setup["order_cancelled_id"]}, headers={"Authorization": "Bearer admin-token"})
    assert res_cancel.status_code == 400
    assert res_cancel.get_json()["error"]["code"] == "INVALID_ORDER_STATE"


def test_duplicate_shipment_prevention(client, admin_user, shipment_setup, monkeypatch):
    """Test duplicate shipment creation calls for same order are idempotent."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    o_id = shipment_setup["order_paid_id"]

    res1 = client.post("/api/v1/shipments/create", json={"order_id": o_id}, headers={"Authorization": "Bearer admin-token"})
    assert res1.status_code == 201

    res2 = client.post("/api/v1/shipments/create", json={"order_id": o_id}, headers={"Authorization": "Bearer admin-token"})
    assert res2.status_code == 200
    assert "already exists" in res2.get_json()["message"].lower()


def test_customer_shipment_tracking_and_idor(client, customer_user_a, customer_user_b, admin_user, shipment_setup, monkeypatch):
    """Test Customer tracking endpoint is IDOR protected."""
    # Create shipment first as Admin
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    res_create = client.post("/api/v1/shipments/create", json={"order_id": shipment_setup["order_paid_id"]}, headers={"Authorization": "Bearer admin-token"})
    shipment_id = res_create.get_json()["data"]["id"]

    # Customer A (owner) tracks shipment -> 200 OK
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_track_a = client.get(f"/api/v1/shipments/{shipment_id}/tracking", headers={"Authorization": "Bearer token-a"})
    assert res_track_a.status_code == 200
    assert res_track_a.get_json()["data"]["shipment"]["awb_code"] is not None

    # Customer B (non-owner) attempts to track -> 403 Forbidden
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_b["supabase_uid"], "email": customer_user_b["email"]},
    )
    res_track_b = client.get(f"/api/v1/shipments/{shipment_id}/tracking", headers={"Authorization": "Bearer token-b"})
    assert res_track_b.status_code == 403


def test_customer_order_detail_includes_shipment(client, customer_user_a, admin_user, shipment_setup, monkeypatch):
    """Test GET /api/v1/orders/<id> enriches response with active shipment snapshot."""
    # Admin creates shipment
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    o_id = shipment_setup["order_paid_id"]
    client.post("/api/v1/shipments/create", json={"order_id": o_id}, headers={"Authorization": "Bearer admin-token"})

    # Customer retrieves order
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    response = client.get(f"/api/v1/orders/{o_id}", headers={"Authorization": "Bearer token-a"})
    assert response.status_code == 200
    shipment_info = response.get_json()["data"]["shipment"]
    assert shipment_info is not None
    assert shipment_info["status"] == "assigned"


def test_shiprocket_webhook_status_sync_and_cod_collection(client, app, admin_user, shipment_setup, monkeypatch):
    """Test Shiprocket Webhook synchronizes status and confirms COD payment collection upon delivery."""
    # 1. Create COD Shipment
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    o_id = shipment_setup["order_cod_id"]
    res_create = client.post("/api/v1/shipments/create", json={"order_id": o_id}, headers={"Authorization": "Bearer admin-token"})
    awb_code = res_create.get_json()["data"]["awb_code"]
    token = app.config["SHIPROCKET_WEBHOOK_TOKEN"]

    # 2. Webhook: IN TRANSIT status event
    payload_transit = {
        "event_id": "evt_sr_001",
        "current_status": "IN TRANSIT",
        "awb": awb_code,
    }
    res_wh1 = client.post(
        "/api/v1/shipments/shiprocket/webhook",
        data=json.dumps(payload_transit),
        content_type="application/json",
        headers={"X-Api-Key": token},
    )
    assert res_wh1.status_code == 200

    with app.app_context():
        order = db.session.get(Order, o_id)
        assert order.order_status == "shipped"

    # 3. Webhook: DELIVERED status event (confirms COD payment)
    payload_delivered = {
        "event_id": "evt_sr_002",
        "current_status": "DELIVERED",
        "awb": awb_code,
        "cod_status": "collected",
    }
    res_wh2 = client.post(
        "/api/v1/shipments/shiprocket/webhook",
        data=json.dumps(payload_delivered),
        content_type="application/json",
        headers={"X-Api-Key": token},
    )
    assert res_wh2.status_code == 200

    with app.app_context():
        order = db.session.get(Order, o_id)
        assert order.order_status == "delivered"
        assert order.payment_status == "paid"
        payment = Payment.query.filter_by(order_id=o_id).first()
        assert payment.status == "captured"


def test_shiprocket_webhook_token_verification_and_idempotency(client, app, admin_user, shipment_setup, monkeypatch):
    """Test webhook rejects invalid token and handles duplicate event IDs idempotently."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    res_create = client.post("/api/v1/shipments/create", json={"order_id": shipment_setup["order_paid_id"]}, headers={"Authorization": "Bearer admin-token"})
    awb_code = res_create.get_json()["data"]["awb_code"]
    token = app.config["SHIPROCKET_WEBHOOK_TOKEN"]

    payload = {"event_id": "evt_sr_dup_99", "current_status": "IN TRANSIT", "awb": awb_code}

    # Invalid token -> 401
    res_invalid = client.post(
        "/api/v1/shipments/shiprocket/webhook",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Api-Key": "invalid_webhook_token"},
    )
    assert res_invalid.status_code == 401

    # Valid token 1st time -> 200
    res1 = client.post(
        "/api/v1/shipments/shiprocket/webhook",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Api-Key": token},
    )
    assert res1.status_code == 200

    # Valid token 2nd time (duplicate event_id) -> 200
    res2 = client.post(
        "/api/v1/shipments/shiprocket/webhook",
        data=json.dumps(payload),
        content_type="application/json",
        headers={"X-Api-Key": token},
    )
    assert res2.status_code == 200
    assert "already processed" in res2.get_json()["message"].lower()
