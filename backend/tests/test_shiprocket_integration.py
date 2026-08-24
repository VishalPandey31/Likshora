import json
import hmac
import hashlib
import pytest
from flask import current_app
from app.models import Order, OrderItem, Address, Product, Category, User, Payment, Shipment, CartItem
from app.extensions import db
from app.services import ShiprocketService


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            supabase_uid="test-sr-user-uid",
            name="SR Test User",
            email="sr_user@example.com",
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
            supabase_uid="test-sr-admin-uid",
            name="SR Admin User",
            email="sr_admin@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def setup_catalog_and_address(app, test_user):
    with app.app_context():
        cat = Category(name="Electronics", slug="electronics", is_active=True)
        db.session.add(cat)
        db.session.commit()

        prod = Product(
            category_id=cat.id,
            name="Wireless Headphones",
            slug="wireless-headphones",
            sku="WH-100",
            price=2500.00,
            stock_quantity=50,
            weight=0.750,
            is_active=True,
        )
        db.session.add(prod)
        db.session.commit()

        addr = Address(
            user_id=test_user["id"],
            full_name="SR Test User",
            phone="9988776655",
            address_line1="45 Tech Park",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            country="India",
            is_default=True,
        )
        db.session.add(addr)
        db.session.commit()

        return {"category_id": cat.id, "product_id": prod.id, "address_id": addr.id}


def make_user_token(supabase_uid, role="customer"):
    import jwt
    from datetime import datetime, timedelta, timezone

    payload = {
        "sub": supabase_uid,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, "likshora-dev-secret-key-change-in-production", algorithm="HS256")


def generate_razorpay_signature(app, order_id, payment_id):
    secret = app.config.get("RAZORPAY_KEY_SECRET", "mock_razorpay_secret_key")
    msg = f"{order_id}|{payment_id}"
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


def test_shiprocket_service_methods(app):
    """Test core ShiprocketService methods in test/mock mode."""
    with app.app_context():
        token = ShiprocketService.get_auth_token()
        assert token == "mock_shiprocket_jwt_token"

        serviceability = ShiprocketService.get_courier_serviceability(
            pickup_postcode="400001",
            delivery_postcode="560001",
            weight=0.5,
            cod=True,
        )
        assert serviceability["status"] == 200
        assert "data" in serviceability

        order_res = ShiprocketService.create_order({
            "order_id": "ORD-TEST-101",
            "order_date": "2026-08-23 10:00",
            "pickup_location": "Primary",
        })
        assert "order_id" in order_res
        assert "shipment_id" in order_res

        awb_res = ShiprocketService.generate_awb(order_res["shipment_id"])
        assert awb_res.get("awb_assign_status") == 1
        assert "awb_code" in awb_res.get("response", {}).get("data", {})

        pickup_res = ShiprocketService.request_pickup([order_res["shipment_id"]])
        assert pickup_res.get("pickup_status") == 1

        track_res = ShiprocketService.track_shipment("AWB-SR-800000")
        assert "tracking_data" in track_res

        label_res = ShiprocketService.generate_label([order_res["shipment_id"]])
        assert label_res.get("status") == 200

        manifest_res = ShiprocketService.generate_manifest([order_res["shipment_id"]])
        assert manifest_res.get("status") == 200


def test_automatic_cod_shiprocket_fulfillment(client, test_user, setup_catalog_and_address, monkeypatch):
    """Test that placing a COD order automatically creates the Shiprocket order & shipment."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": test_user["supabase_uid"], "email": test_user["email"]},
    )
    headers = {"Authorization": "Bearer mock-token"}

    # Add item to cart
    cart_resp = client.post(
        "/api/v1/cart",
        json={"product_id": setup_catalog_and_address["product_id"], "quantity": 2},
        headers=headers,
    )
    assert cart_resp.status_code == 201

    # Place COD order
    order_resp = client.post(
        "/api/v1/orders",
        json={"address_id": setup_catalog_and_address["address_id"], "payment_method": "cod"},
        headers=headers,
    )
    assert order_resp.status_code == 201
    order_data = order_resp.get_json()["data"]
    order_id = order_data["id"]

    # Verify Shipment automatically created in DB
    shipment = Shipment.query.filter_by(order_id=order_id).first()
    assert shipment is not None
    assert shipment.provider == "shiprocket"
    assert shipment.awb_code is not None
    assert shipment.status in ["assigned", "pickup_scheduled"]
    assert shipment.pickup_token_number is not None


def test_prepaid_payment_verification_auto_fulfillment(client, app, test_user, setup_catalog_and_address, monkeypatch):
    """Test that server-side Razorpay payment verification triggers automatic Shiprocket fulfillment."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": test_user["supabase_uid"], "email": test_user["email"]},
    )
    headers = {"Authorization": "Bearer mock-token"}

    # Add item to cart and create online order
    client.post(
        "/api/v1/cart",
        json={"product_id": setup_catalog_and_address["product_id"], "quantity": 1},
        headers=headers,
    )
    order_resp = client.post(
        "/api/v1/orders",
        json={"address_id": setup_catalog_and_address["address_id"], "payment_method": "online"},
        headers=headers,
    )
    assert order_resp.status_code == 201
    order_id = order_resp.get_json()["data"]["id"]

    # Create Razorpay order
    rzp_resp = client.post(
        "/api/v1/payments/create-order",
        json={"order_id": order_id},
        headers=headers,
    )
    assert rzp_resp.status_code == 200
    rzp_order_id = rzp_resp.get_json()["razorpay_order_id"]
    rzp_payment_id = "pay_mock_123456"
    sig = generate_razorpay_signature(app, rzp_order_id, rzp_payment_id)

    # Verify Razorpay payment
    verify_resp = client.post(
        "/api/v1/payments/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": rzp_payment_id,
            "razorpay_signature": sig,
        },
        headers=headers,
    )
    assert verify_resp.status_code == 200

    # Verify Shipment automatically created in DB
    shipment = Shipment.query.filter_by(order_id=order_id).first()
    assert shipment is not None
    assert shipment.provider == "shiprocket"
    assert shipment.awb_code is not None


def test_shiprocket_idempotency_protection(app, test_user, setup_catalog_and_address):
    """Verify that calling fulfill_order_in_shiprocket multiple times returns the existing shipment without duplication."""
    with app.app_context():
        order = Order(
            user_id=test_user["id"],
            address_id=setup_catalog_and_address["address_id"],
            order_number="ORD-IDEMPOTENT-01",
            subtotal=2500.00,
            total_amount=2500.00,
            payment_method="cod",
            payment_status="pending",
            order_status="confirmed",
            shipping_full_name="SR Test User",
            shipping_phone="9988776655",
            shipping_address_line1="45 Tech Park",
            shipping_city="Bengaluru",
            shipping_state="Karnataka",
            shipping_postal_code="560001",
            shipping_country="India",
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=setup_catalog_and_address["product_id"],
            product_name="Wireless Headphones",
            sku="WH-100",
            quantity=1,
            unit_price=2500.00,
            subtotal=2500.00,
        )
        db.session.add(item)
        db.session.commit()

        # First fulfillment
        s1, _ = ShiprocketService.fulfill_order_in_shiprocket(order)
        awb_1 = s1.awb_code

        # Second fulfillment retry
        s2, _ = ShiprocketService.fulfill_order_in_shiprocket(order)
        assert s2.id == s1.id
        assert s2.awb_code == awb_1

        shipment_count = Shipment.query.filter_by(order_id=order.id).count()
        assert shipment_count == 1


def test_shiprocket_webhook_status_update(client, app, test_user, setup_catalog_and_address, monkeypatch):
    """Test receiving a Shiprocket webhook and verifying shipment/order status updates."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": test_user["supabase_uid"], "email": test_user["email"]},
    )
    headers = {"Authorization": "Bearer mock-token"}

    client.post(
        "/api/v1/cart",
        json={"product_id": setup_catalog_and_address["product_id"], "quantity": 1},
        headers=headers,
    )
    order_resp = client.post(
        "/api/v1/orders",
        json={"address_id": setup_catalog_and_address["address_id"], "payment_method": "cod"},
        headers=headers,
    )
    order_id = order_resp.get_json()["data"]["id"]
    shipment = Shipment.query.filter_by(order_id=order_id).first()

    webhook_token = app.config.get("SHIPROCKET_WEBHOOK_TOKEN", "mock_shiprocket_webhook_token")
    webhook_headers = {"X-Api-Key": webhook_token}
    webhook_payload = {
        "event_id": "evt_mock_sr_delivered_101",
        "awb": shipment.awb_code,
        "current_status": "DELIVERED",
        "location": "Bengaluru Hub",
        "cod_status": "collected",
    }

    wh_resp = client.post("/api/v1/shipments/shiprocket/webhook", json=webhook_payload, headers=webhook_headers)
    assert wh_resp.status_code == 200

    updated_shipment = db.session.get(Shipment, shipment.id)
    assert updated_shipment.status == "delivered"
    assert updated_shipment.order.order_status == "delivered"
    assert updated_shipment.order.payment_status == "paid"


def test_admin_shiprocket_actions(client, admin_user, test_user, setup_catalog_and_address, monkeypatch):
    """Test admin manual retry, pickup request, label, and manifest generation endpoints."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    admin_headers = {"Authorization": "Bearer mock-admin-token"}

    # Create paid order manually
    with client.application.app_context():
        order = Order(
            user_id=test_user["id"],
            address_id=setup_catalog_and_address["address_id"],
            order_number="ORD-ADMIN-RETRY-01",
            subtotal=2500.00,
            total_amount=2500.00,
            payment_method="online",
            payment_status="paid",
            order_status="confirmed",
            shipping_full_name="SR Test User",
            shipping_phone="9988776655",
            shipping_address_line1="45 Tech Park",
            shipping_city="Bengaluru",
            shipping_state="Karnataka",
            shipping_postal_code="560001",
            shipping_country="India",
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=setup_catalog_and_address["product_id"],
            product_name="Wireless Headphones",
            sku="WH-100",
            quantity=1,
            unit_price=2500.00,
            subtotal=2500.00,
        )
        db.session.add(item)
        db.session.commit()
        order_id = order.id

    # Admin manual fulfillment trigger
    fulfill_resp = client.post(f"/api/v1/admin/orders/{order_id}/fulfill-shiprocket", headers=admin_headers)
    assert fulfill_resp.status_code == 200
    shipment_data = fulfill_resp.get_json()["data"]
    shipment_id = shipment_data["id"]

    # Admin request pickup
    pickup_resp = client.post(f"/api/v1/admin/shipments/{shipment_id}/request-pickup", headers=admin_headers)
    assert pickup_resp.status_code == 200

    # Admin generate label
    label_resp = client.post(f"/api/v1/admin/shipments/{shipment_id}/generate-label", headers=admin_headers)
    assert label_resp.status_code == 200
    assert "label_url" in label_resp.get_json()

    # Admin generate manifest
    manifest_resp = client.post(f"/api/v1/admin/shipments/{shipment_id}/generate-manifest", headers=admin_headers)
    assert manifest_resp.status_code == 200
    assert "manifest_url" in manifest_resp.get_json()
