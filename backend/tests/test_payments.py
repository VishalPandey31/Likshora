import hmac
import hashlib
import json
import pytest
from app.models import Order, OrderItem, Address, Product, Category, User, Payment, PaymentWebhookEvent
from app.extensions import db
from app.api.payments import verify_razorpay_hmac_signature


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-pay-a-uid",
            name="Customer Pay A",
            email="pay_a@example.com",
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
            supabase_uid="test-customer-pay-b-uid",
            name="Customer Pay B",
            email="pay_b@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def payment_setup(app, customer_user_a, customer_user_b):
    with app.app_context():
        cat = Category(name="Electronics", slug="electronics", is_active=True)
        db.session.add(cat)
        db.session.commit()

        addr_a = Address(
            user_id=customer_user_a["id"],
            full_name="Customer Pay A",
            phone="9876543210",
            address_line1="100 Tech Park",
            city="Bangalore",
            state="Karnataka",
            postal_code="560001",
            country="India",
            is_default=True,
        )
        db.session.add(addr_a)
        db.session.commit()

        # Online Order for User A
        order_online = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-2026-ONLINE",
            subtotal=1500.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1500.00,
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
        # COD Order for User A
        order_cod = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-2026-COD",
            subtotal=1000.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1000.00,
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
        # Paid Order for User A
        order_paid = Order(
            user_id=customer_user_a["id"],
            address_id=addr_a.id,
            order_number="ORD-2026-PAID",
            subtotal=2000.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=2000.00,
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
        db.session.add_all([order_online, order_cod, order_paid])
        db.session.commit()

        return {
            "order_online_id": order_online.id,
            "order_cod_id": order_cod.id,
            "order_paid_id": order_paid.id,
        }


def generate_webhook_signature(app, payload_bytes: bytes) -> str:
    """Helper to generate valid HMAC-SHA256 signature for test webhook payload."""
    secret = app.config["RAZORPAY_WEBHOOK_SECRET"]
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


# -----------------------------------------------------------------------------
# WEBHOOK MANDATORY TEST SUITE (TESTS 1 to 10)
# -----------------------------------------------------------------------------

def test_webhook_1_valid_signature_event_processed(client, app, customer_user_a, payment_setup, monkeypatch):
    """TEST 1: Valid webhook signature -> 200, event processed."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    payload = {
        "event_id": "evt_test_001",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_test_001", "order_id": rzp_order_id, "amount": 150000, "status": "captured"}}},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_webhook_signature(app, body)

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    with app.app_context():
        order = db.session.get(Order, payment_setup["order_online_id"])
        assert order.payment_status == "paid"
        assert order.order_status in ["confirmed", "processing"]


def test_webhook_2_invalid_signature_rejected(client, app):
    """TEST 2: Invalid webhook signature -> 400, database unchanged."""
    payload = {"event_id": "evt_fake_sig", "event": "payment.captured"}
    body = json.dumps(payload).encode("utf-8")

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": "invalid_sig_hex"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False
    assert response.get_json()["message"] == "Invalid webhook signature"


def test_webhook_3_missing_signature_rejected(client):
    """TEST 3: Missing signature header -> rejected (400)."""
    payload = {"event_id": "evt_no_sig", "event": "payment.captured"}
    body = json.dumps(payload).encode("utf-8")

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_webhook_4_duplicate_event_id_idempotency(client, app, customer_user_a, payment_setup, monkeypatch):
    """TEST 4: Duplicate event ID -> 200, no duplicate processing."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    payload = {
        "event_id": "evt_duplicate_id_004",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_dup_004", "order_id": rzp_order_id}}},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_webhook_signature(app, body)

    # First delivery
    res1 = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert res1.status_code == 200

    # Second delivery
    res2 = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert res2.status_code == 200
    assert "already processed" in res2.get_json()["message"].lower()


def test_webhook_5_payment_captured_updates_payment_and_order(client, app, customer_user_a, payment_setup, monkeypatch):
    """TEST 5: payment.captured -> payment.status = captured, order.payment_status = paid."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    payload = {
        "event_id": "evt_captured_005",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_cap_005", "order_id": rzp_order_id}}},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_webhook_signature(app, body)

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert response.status_code == 200

    with app.app_context():
        p = Payment.query.filter_by(provider_order_id=rzp_order_id).first()
        assert p.status == "captured"
        assert p.order.payment_status == "paid"
        # Verify order_status is confirmed/processing, NOT shipped/delivered
        assert p.order.order_status in ["confirmed", "processing"]


def test_webhook_6_payment_failed_updates_payment_and_order(client, app, customer_user_a, payment_setup, monkeypatch):
    """TEST 6: payment.failed -> payment.status = failed, order.payment_status = failed (NOT paid)."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    payload = {
        "event_id": "evt_failed_006",
        "event": "payment.failed",
        "payload": {"payment": {"entity": {"id": "pay_fail_006", "order_id": rzp_order_id, "error_description": "Card declined"}}},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_webhook_signature(app, body)

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert response.status_code == 200

    with app.app_context():
        p = Payment.query.filter_by(provider_order_id=rzp_order_id).first()
        assert p.status == "failed"
        assert p.order.payment_status == "failed"


def test_webhook_7_order_paid_synchronizes_payment_and_order(client, app, customer_user_a, payment_setup, monkeypatch):
    """TEST 7: order.paid -> payment/order synchronized."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    payload = {
        "event_id": "evt_order_paid_007",
        "event": "order.paid",
        "payload": {"payment": {"entity": {"id": "pay_ord_paid_007", "order_id": rzp_order_id}}},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_webhook_signature(app, body)

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert response.status_code == 200

    with app.app_context():
        p = Payment.query.filter_by(provider_order_id=rzp_order_id).first()
        assert p.status == "captured"
        assert p.order.payment_status == "paid"


def test_webhook_8_unknown_event_returns_200_without_db_modification(client, app):
    """TEST 8: Unknown event -> 200, no database modification to order/payment."""
    payload = {
        "event_id": "evt_unknown_008",
        "event": "payment.dispute.created",
        "payload": {"dispute": {"id": "disp_123"}},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_webhook_signature(app, body)

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_webhook_9_unknown_payment_mapping_safely_handled(client, app):
    """TEST 9: Unknown payment mapping -> safely handled without creating dummy orders/payments."""
    payload = {
        "event_id": "evt_unmapped_009",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_unmapped", "order_id": "order_non_existent_999"}}},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = generate_webhook_signature(app, body)

    response = client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert response.status_code == 200

    with app.app_context():
        assert Payment.query.filter_by(provider_order_id="order_non_existent_999").first() is None


def test_webhook_10_late_event_cannot_downgrade_captured_payment(client, app, customer_user_a, payment_setup, monkeypatch):
    """TEST 10: Late event (payment.failed) cannot downgrade an already captured payment."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    # 1. Capture payment first
    payload1 = {
        "event_id": "evt_cap_first_010",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_010", "order_id": rzp_order_id}}},
    }
    body1 = json.dumps(payload1).encode("utf-8")
    sig1 = generate_webhook_signature(app, body1)
    client.post("/api/v1/payments/razorpay/webhook", data=body1, content_type="application/json", headers={"X-Razorpay-Signature": sig1})

    # 2. Late failed event arrives
    payload2 = {
        "event_id": "evt_late_failed_010",
        "event": "payment.failed",
        "payload": {"payment": {"entity": {"id": "pay_010", "order_id": rzp_order_id}}},
    }
    body2 = json.dumps(payload2).encode("utf-8")
    sig2 = generate_webhook_signature(app, body2)
    res2 = client.post("/api/v1/payments/razorpay/webhook", data=body2, content_type="application/json", headers={"X-Razorpay-Signature": sig2})
    assert res2.status_code == 200

    # Verify payment remains 'captured' and order remains 'paid'
    with app.app_context():
        p = Payment.query.filter_by(provider_order_id=rzp_order_id).first()
        assert p.status == "captured"
        assert p.order.payment_status == "paid"


# -----------------------------------------------------------------------------
# ADDITIONAL VERIFICATION SECURITY TESTS
# -----------------------------------------------------------------------------

def test_verify_customer_ownership_protection(client, app, customer_user_a, customer_user_b, payment_setup, monkeypatch):
    """Customer B cannot submit Customer A's Razorpay order ID to get order marked as paid (IDOR protection)."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    # User A creates Razorpay order
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    # User B attempts to verify User A's Razorpay order
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_b["supabase_uid"], "email": customer_user_b["email"]},
    )
    res_verify = client.post(
        "/api/v1/payments/razorpay/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": "pay_mock_user_b",
            "razorpay_signature": "sig_mock",
        },
        headers={"Authorization": "Bearer token-b"},
    )
    assert res_verify.status_code == 404
    assert res_verify.get_json()["error"]["code"] == "PAYMENT_NOT_FOUND"


def test_verify_order_id_mismatch_rejected(client, app, customer_user_a, payment_setup, monkeypatch):
    """Passing mismatched internal order_id during verification is rejected."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    res_verify = client.post(
        "/api/v1/payments/razorpay/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": "pay_mock_mismatch",
            "razorpay_signature": "sig_mock",
            "order_id": 999999,
        },
        headers={"Authorization": "Bearer token-a"},
    )
    assert res_verify.status_code == 400
    assert res_verify.get_json()["error"]["code"] == "ORDER_MISMATCH"


def test_verify_amount_mismatch_rejected(client, app, customer_user_a, payment_setup, monkeypatch):
    """When Razorpay API returns payment with mismatched amount, verification is rejected."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    # Mock signature verification success
    monkeypatch.setattr("app.services.razorpay_service.RazorpayService.verify_payment_signature", lambda o, p, s: True)
    # Mock fetch_payment returning tampered amount (10000 paise instead of 150000 paise)
    monkeypatch.setattr("app.services.razorpay_service.RazorpayService.fetch_payment", lambda pid: {"id": pid, "amount": 10000, "status": "captured"})

    res_verify = client.post(
        "/api/v1/payments/razorpay/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": "pay_tampered_amount",
            "razorpay_signature": "valid_mock_sig",
        },
        headers={"Authorization": "Bearer token-a"},
    )
    assert res_verify.status_code == 400
    assert res_verify.get_json()["error"]["code"] == "AMOUNT_MISMATCH"

    with app.app_context():
        order = db.session.get(Order, payment_setup["order_online_id"])
        assert order.payment_status == "failed"


def test_verify_duplicate_request_idempotency(client, app, customer_user_a, payment_setup, monkeypatch):
    """Duplicate payment verification requests return success without re-processing."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": payment_setup["order_online_id"]}, headers={"Authorization": "Bearer token-a"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    monkeypatch.setattr("app.services.razorpay_service.RazorpayService.verify_payment_signature", lambda o, p, s: True)

    # First verification
    res1 = client.post(
        "/api/v1/payments/razorpay/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": "pay_idempotent_01",
            "razorpay_signature": "sig_mock",
        },
        headers={"Authorization": "Bearer token-a"},
    )
    assert res1.status_code == 200
    assert res1.get_json()["success"] is True

    # Duplicate verification
    res2 = client.post(
        "/api/v1/payments/razorpay/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": "pay_idempotent_01",
            "razorpay_signature": "sig_mock",
        },
        headers={"Authorization": "Bearer token-a"},
    )
    assert res2.status_code == 200
    assert "already verified" in res2.get_json()["message"].lower()

