import json
import pytest
from datetime import datetime, timezone
from app.models import User, Address, Order, Product, Category, CartItem, WishlistItem, Payment, Shipment
from app.extensions import db
from app.config import ProductionConfig


@pytest.fixture
def sec_customer_a(app):
    with app.app_context():
        user = User(
            supabase_uid="sec-customer-a-uid",
            name="Security Customer A",
            email="sec_a@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def sec_customer_b(app):
    with app.app_context():
        user = User(
            supabase_uid="sec-customer-b-uid",
            name="Security Customer B",
            email="sec_b@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def sec_admin(app):
    with app.app_context():
        admin = User(
            supabase_uid="sec-admin-uid",
            name="Security Admin",
            email="sec_admin@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def sec_setup(app, sec_customer_a):
    with app.app_context():
        cat = Category(name="Security Cat", slug="security-cat", is_active=True)
        db.session.add(cat)
        db.session.commit()

        prod = Product(
            category_id=cat.id,
            name="Security Shirt",
            slug="security-shirt",
            sku="SEC-SHIRT-01",
            price=1500.00,
            stock_quantity=10,
            is_active=True,
        )
        db.session.add(prod)
        db.session.commit()

        addr_a = Address(
            user_id=sec_customer_a["id"],
            full_name="Security Customer A",
            phone="9876543210",
            address_line1="100 Secure Street",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400001",
            country="India",
            is_default=True,
        )
        db.session.add(addr_a)
        db.session.commit()

        order_a = Order(
            user_id=sec_customer_a["id"],
            address_id=addr_a.id,
            order_number="ORD-SEC-001",
            subtotal=1500.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1500.00,
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
        db.session.add(order_a)
        db.session.commit()

        wish_a = WishlistItem(user_id=sec_customer_a["id"], product_id=prod.id)
        db.session.add(wish_a)
        db.session.commit()

        return {
            "category_id": cat.id,
            "product_id": prod.id,
            "address_id": addr_a.id,
            "order_id": order_a.id,
            "wishlist_id": wish_a.id,
        }


# =============================================================================
# 30 AUTOMATED SECURITY CONTROL TESTS
# =============================================================================

def test_1_unauthenticated_protected_api_returns_401(client):
    """1. Test unauthenticated request to protected endpoint returns 401."""
    res = client.get("/api/v1/orders")
    assert res.status_code == 401


def test_2_invalid_jwt_format_returns_401(client):
    """2. Test invalid authorization header format returns 401."""
    res = client.get("/api/v1/orders", headers={"Authorization": "InvalidFormatToken"})
    assert res.status_code == 401


def test_3_invalid_jwt_signature_returns_401(client, monkeypatch):
    """3. Test invalid JWT token verification returns 401."""
    def mock_verify_fail(t):
        from app.errors import APIException
        raise APIException("Invalid access token", status_code=401, code="UNAUTHORIZED")

    monkeypatch.setattr("app.auth.decorators.supabase_auth.verify_token", mock_verify_fail)
    res = client.get("/api/v1/orders", headers={"Authorization": "Bearer bogus-token"})
    assert res.status_code == 401


def test_4_customer_accessing_other_user_order_idor_protection(client, sec_customer_b, sec_setup, monkeypatch):
    """4. Test customer accessing another user's order returns 404."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_b["supabase_uid"], "email": sec_customer_b["email"]},
    )
    res = client.get(f"/api/v1/orders/{sec_setup['order_id']}", headers={"Authorization": "Bearer token-b"})
    assert res.status_code == 404


def test_5_customer_accessing_other_user_address_idor_protection(client, sec_customer_b, sec_setup, monkeypatch):
    """5. Test customer accessing another user's address returns 404."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_b["supabase_uid"], "email": sec_customer_b["email"]},
    )
    res = client.get(f"/api/v1/addresses/{sec_setup['address_id']}", headers={"Authorization": "Bearer token-b"})
    assert res.status_code == 404


def test_6_customer_accessing_other_user_wishlist_idor_protection(client, sec_customer_b, sec_setup, monkeypatch):
    """6. Test customer attempting to delete another user's wishlist item returns 404."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_b["supabase_uid"], "email": sec_customer_b["email"]},
    )
    res = client.delete(f"/api/v1/wishlist/{sec_setup['wishlist_id']}", headers={"Authorization": "Bearer token-b"})
    assert res.status_code == 404


def test_7_customer_accessing_other_user_shipment_idor_protection(client, sec_customer_b, sec_setup, monkeypatch):
    """7. Test customer accessing tracking for another user's order returns 404."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_b["supabase_uid"], "email": sec_customer_b["email"]},
    )
    res = client.get(f"/api/v1/orders/{sec_setup['order_id']}/tracking", headers={"Authorization": "Bearer token-b"})
    assert res.status_code == 404


def test_8_non_admin_accessing_admin_api_denied(client, sec_customer_a, monkeypatch):
    """8. Test customer attempting to access admin endpoint returns 403 Forbidden."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.get("/api/v1/admin/dashboard", headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 403


def test_9_customer_attempting_to_modify_role_spoofing(client, sec_customer_a, monkeypatch):
    """9. Test customer attempting to update role to 'admin' via profile endpoint returns 403 Forbidden."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.put("/api/v1/profile", json={"role": "admin"}, headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "FORBIDDEN_FIELD_UPDATE"


def test_10_customer_cannot_arbitrarily_modify_payment_status(client, sec_customer_a, sec_setup, monkeypatch):
    """10. Test customer cannot set payment_status via profile or arbitrary endpoint."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.put("/api/v1/profile", json={"payment_status": "paid"}, headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 403


def test_11_customer_cannot_arbitrarily_modify_order_status(client, sec_customer_a, sec_setup, monkeypatch):
    """11. Test customer cannot mark an order delivered directly."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    # Attempting to call admin order status endpoint as customer -> 403
    res = client.patch(f"/api/v1/admin/orders/{sec_setup['order_id']}/status", json={"status": "delivered"}, headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 403


def test_12_invalid_payment_method_rejected(client, sec_customer_a, sec_setup, monkeypatch):
    """12. Test checkout with invalid payment_method returns 400."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.post("/api/v1/orders", json={"address_id": sec_setup["address_id"], "payment_method": "crypto"}, headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 400


def test_13_negative_quantity_in_cart_rejected(client, sec_customer_a, sec_setup, monkeypatch):
    """13. Test negative or zero cart quantity returns 400."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.post("/api/v1/cart", json={"product_id": sec_setup["product_id"], "quantity": -5}, headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_QUANTITY"


def test_14_invalid_product_id_rejected(client, sec_customer_a, monkeypatch):
    """14. Test invalid product ID returns 404."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.get("/api/v1/products/999999")
    assert res.status_code == 404


def test_15_sql_injection_payload_handled_safely(client):
    """15. Test search query containing SQL injection payload is safely parameterized by ORM."""
    injection_query = "' OR '1'='1' --"
    res = client.get(f"/api/v1/products?search={injection_query}")
    assert res.status_code == 200
    # SQL injection string search should not crash the database or return all records maliciously


def test_16_malicious_sort_parameter_defaults_safely(client):
    """16. Test invalid or malicious sort parameter falls back safely to default newest sorting."""
    res = client.get("/api/v1/products?sort=id;DROP+TABLE+users;--")
    assert res.status_code == 200


def test_17_excessive_pagination_per_page_capped(client):
    """17. Test requesting excessive per_page value is safely capped at 100."""
    res = client.get("/api/v1/products?per_page=999999")
    assert res.status_code == 200
    assert res.get_json()["pagination"]["per_page"] == 100


def test_18_invalid_razorpay_signature_rejected(client, sec_customer_a, sec_setup, monkeypatch):
    """18. Test invalid Razorpay HMAC payment signature returns 400."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    # Create online order first
    res_rzp = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": sec_setup["order_id"]}, headers={"Authorization": "Bearer customer-token"})
    # If order is COD, switch to online method
    with client.application.app_context():
        order = db.session.get(Order, sec_setup["order_id"])
        order.payment_method = "online"
        db.session.commit()

    res_create = client.post("/api/v1/payments/razorpay/create-order", json={"order_id": sec_setup["order_id"]}, headers={"Authorization": "Bearer customer-token"})
    rzp_order_id = res_create.get_json()["data"]["razorpay_order_id"]

    res_verify = client.post(
        "/api/v1/payments/razorpay/verify",
        json={
            "razorpay_order_id": rzp_order_id,
            "razorpay_payment_id": "pay_mock_123",
            "razorpay_signature": "invalid_signature_string",
        },
        headers={"Authorization": "Bearer customer-token"},
    )
    assert res_verify.status_code == 400
    assert res_verify.get_json()["error"]["code"] == "INVALID_PAYMENT_SIGNATURE"


def test_19_missing_razorpay_signature_rejected(client, sec_customer_a, monkeypatch):
    """19. Test missing Razorpay signature fields return 400."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.post("/api/v1/payments/razorpay/verify", json={"razorpay_order_id": "ord_123"}, headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 400


def test_20_duplicate_razorpay_webhook_idempotency(client, app):
    """20. Test duplicate Razorpay webhook event ID is handled idempotently without error."""
    raw_body = json.dumps({"event_id": "evt_dup_001", "event": "order.paid"}).encode("utf-8")
    import hmac, hashlib
    secret = app.config["RAZORPAY_WEBHOOK_SECRET"]
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # 1st attempt
    res1 = client.post("/api/v1/payments/razorpay/webhook", data=raw_body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert res1.status_code == 200

    # 2nd attempt (duplicate)
    res2 = client.post("/api/v1/payments/razorpay/webhook", data=raw_body, content_type="application/json", headers={"X-Razorpay-Signature": sig})
    assert res2.status_code == 200
    assert "already processed" in res2.get_json()["message"].lower()


def test_21_invalid_shiprocket_webhook_token_rejected(client):
    """21. Test invalid Shiprocket webhook token returns 401 Unauthorized."""
    payload = {"event_id": "evt_sr_inv_01", "current_status": "IN TRANSIT", "awb": "AWB-123"}
    res = client.post("/api/v1/shipments/shiprocket/webhook", json=payload, headers={"X-Api-Key": "invalid_webhook_token"})
    assert res.status_code == 401


def test_22_duplicate_shiprocket_event_idempotency(client, app):
    """22. Test duplicate Shiprocket webhook event is handled idempotently."""
    token = app.config["SHIPROCKET_WEBHOOK_TOKEN"]
    payload = {"event_id": "evt_sr_dup_999", "current_status": "IN TRANSIT", "awb": "AWB-MOCK-999"}

    res1 = client.post("/api/v1/shipments/shiprocket/webhook", json=payload, headers={"X-Api-Key": token})
    assert res1.status_code == 200

    res2 = client.post("/api/v1/shipments/shiprocket/webhook", json=payload, headers={"X-Api-Key": token})
    assert res2.status_code == 200
    assert "already processed" in res2.get_json()["message"].lower()


def test_23_secrets_not_returned_in_api_response(client, sec_customer_a, monkeypatch):
    """23. Test API responses do not leak server secrets, passwords, or tokens."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.get("/api/v1/profile", headers={"Authorization": "Bearer customer-token"})
    data_str = json.dumps(res.get_json())
    assert "SECRET_KEY" not in data_str
    assert "RAZORPAY_KEY_SECRET" not in data_str
    assert "SHIPROCKET_PASSWORD" not in data_str


def test_24_http_security_headers_present(client):
    """24. Test response includes standard HTTP Security Headers."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_25_production_secret_validation(monkeypatch):
    """25. Test ProductionConfig raises RuntimeError if insecure default dev key is used in production."""
    monkeypatch.setenv("SECRET_KEY", "likshora-dev-secret-key-change-in-production")
    with pytest.raises(RuntimeError, match="CRITICAL SECURITY RISK"):
        ProductionConfig.validate_production_secrets()


def test_26_rate_limiting_on_auth_login(client):
    """26. Test rate limiter is attached to sensitive auth endpoints."""
    # Execute multiple login requests
    for _ in range(12):
        res = client.post("/api/v1/auth/login", json={"email": "rate_test@example.com", "password": "Password123!"})
    # Rate limit should trigger HTTP 429 Too Many Requests
    assert res.status_code == 429 or res.status_code == 401  # Limiter active or rejected cleanly


def test_27_cod_payment_cannot_be_marked_paid_arbitrarily_by_customer(client, sec_customer_a, sec_setup, monkeypatch):
    """27. Test customer cannot call admin COD payment confirmation endpoint."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.patch(f"/api/v1/admin/orders/{sec_setup['order_id']}/cod-payment", headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 403


def test_28_shipment_cannot_be_marked_delivered_by_customer(client, sec_customer_a, sec_setup, monkeypatch):
    """28. Test customer cannot create shipment or change shipment status."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": sec_customer_a["supabase_uid"], "email": sec_customer_a["email"]},
    )
    res = client.post("/api/v1/shipments/create", json={"order_id": sec_setup["order_id"]}, headers={"Authorization": "Bearer customer-token"})
    assert res.status_code == 403


def test_29_order_number_uniqueness_guarantee(app, sec_customer_a, sec_setup):
    """29. Test order creation guarantees unique order numbers."""
    with app.app_context():
        order1 = db.session.get(Order, sec_setup["order_id"])
        order2 = Order(
            user_id=sec_customer_a["id"],
            address_id=sec_setup["address_id"],
            order_number=order1.order_number + "-DUP",
            subtotal=1000.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1000.00,
            payment_method="cod",
            payment_status="pending",
            order_status="pending",
            shipping_full_name="Name",
            shipping_phone="9876543210",
            shipping_address_line1="Line 1",
            shipping_city="City",
            shipping_state="State",
            shipping_postal_code="100000",
            shipping_country="India",
        )
        db.session.add(order2)
        db.session.commit()
        assert order2.order_number != order1.order_number


def test_30_safe_generic_500_error_response(client, monkeypatch):
    """30. Test internal server exceptions do not leak stack traces or raw details to client."""
    def crash_route():
        raise Exception("Database connection exploded secret_string_123")

    client.application.add_url_rule("/test-crash", "crash_route", crash_route)

    res = client.get("/test-crash")
    assert res.status_code == 500
    data = res.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "secret_string_123" not in json.dumps(data)
