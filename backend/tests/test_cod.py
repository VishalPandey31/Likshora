import hmac
import hashlib
import json
import pytest
from app.models import Order, OrderItem, Address, CartItem, Product, Category, Coupon, User, Payment, PaymentWebhookEvent
from app.extensions import db


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-cod-a-uid",
            name="COD Customer A",
            email="cod_a@example.com",
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
            supabase_uid="test-customer-cod-b-uid",
            name="COD Customer B",
            email="cod_b@example.com",
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
            supabase_uid="test-admin-cod-uid",
            name="Admin Operator",
            email="admincod@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def cod_setup(app, customer_user_a, customer_user_b):
    with app.app_context():
        cat = Category(name="Footwear", slug="footwear", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p1 = Product(
            category_id=cat.id,
            name="Running Shoes",
            slug="running-shoes",
            sku="SHS-RUN-01",
            price=2000.00,
            stock_quantity=10,
            is_active=True,
        )
        p_out = Product(
            category_id=cat.id,
            name="Sold Out Boots",
            slug="sold-out-boots",
            sku="SHS-OUT-02",
            price=3000.00,
            stock_quantity=0,
            is_active=True,
        )
        db.session.add_all([p1, p_out])
        db.session.commit()

        addr_a = Address(
            user_id=customer_user_a["id"],
            full_name="COD Customer A",
            phone="9876543210",
            address_line1="500 MG Road",
            city="Pune",
            state="Maharashtra",
            postal_code="411001",
            country="India",
            is_default=True,
        )
        addr_b = Address(
            user_id=customer_user_b["id"],
            full_name="COD Customer B",
            phone="9999999999",
            address_line1="600 FC Road",
            city="Pune",
            state="Maharashtra",
            postal_code="411004",
            country="India",
            is_default=True,
        )
        db.session.add_all([addr_a, addr_b])
        db.session.commit()

        coupon = Coupon(
            code="FLAT100",
            discount_type="fixed",
            discount_value=100.00,
            minimum_order_amount=1000.00,
            per_user_limit=1,
            is_active=True,
        )
        db.session.add(coupon)
        db.session.commit()

        return {
            "p1_id": p1.id,
            "p_out_id": p_out.id,
            "addr_a_id": addr_a.id,
            "addr_b_id": addr_b.id,
            "coupon_code": coupon.code,
        }


# -----------------------------------------------------------------------------
# COD TEST SUITE (Tests 1 to 24)
# -----------------------------------------------------------------------------

def test_cod_order_creation_success(client, app, customer_user_a, cod_setup, monkeypatch):
    """TEST 1-5, 8, 15, 16, 17: Valid COD order checkout, initial states, stock deduction, and cart clearing."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = cod_setup["p1_id"]

    # Add item to cart
    client.post("/api/v1/cart", json={"product_id": p1_id, "quantity": 2}, headers={"Authorization": "Bearer token-a"})

    # Create COD Order
    response = client.post(
        "/api/v1/orders",
        json={"address_id": cod_setup["addr_a_id"], "payment_method": "cod", "coupon_code": cod_setup["coupon_code"]},
        headers={"Authorization": "Bearer token-a"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]

    # Assert COD order properties
    assert data["payment_method"] == "cod"
    assert data["payment_status"] == "pending"
    assert data["order_status"] == "pending"
    assert data["subtotal"] == 4000.0
    assert data["discount_amount"] == 100.0
    assert data["total_amount"] == 3900.0

    # Verify Payment record in DB has NULL Razorpay fields
    with app.app_context():
        order_id = data["id"]
        payment = Payment.query.filter_by(order_id=order_id).first()
        assert payment is not None
        assert payment.payment_method == "cod"
        assert payment.provider == "cod"
        assert payment.status == "pending"
        assert payment.provider_order_id is None
        assert payment.provider_payment_id is None
        assert payment.razorpay_signature is None

        # Verify stock deducted (10 - 2 = 8) exactly once
        prod = db.session.get(Product, p1_id)
        assert prod.stock_quantity == 8

        # Verify cart cleared
        cart_count = CartItem.query.filter_by(user_id=customer_user_a["id"]).count()
        assert cart_count == 0


def test_cod_order_cannot_create_razorpay_order(client, customer_user_a, cod_setup, monkeypatch):
    """TEST 6, 7: COD order rejects Razorpay order creation calls."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    # Create COD order
    client.post("/api/v1/cart", json={"product_id": cod_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})
    res_ord = client.post("/api/v1/orders", json={"address_id": cod_setup["addr_a_id"], "payment_method": "cod"}, headers={"Authorization": "Bearer token-a"})
    cod_order_id = res_ord.get_json()["data"]["id"]

    # Attempt to create Razorpay Order for COD order -> 400
    res_rzp = client.post(
        "/api/v1/payments/razorpay/create-order",
        json={"order_id": cod_order_id},
        headers={"Authorization": "Bearer token-a"},
    )
    assert res_rzp.status_code == 400
    assert res_rzp.get_json()["error"]["code"] == "INVALID_PAYMENT_METHOD"


def test_online_payment_flow_remains_intact(client, customer_user_a, cod_setup, monkeypatch):
    """TEST 9, 10: Online payment flow works and creates Razorpay Order."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post("/api/v1/cart", json={"product_id": cod_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})
    res_ord = client.post("/api/v1/orders", json={"address_id": cod_setup["addr_a_id"], "payment_method": "online"}, headers={"Authorization": "Bearer token-a"})
    online_order_id = res_ord.get_json()["data"]["id"]

    res_rzp = client.post(
        "/api/v1/payments/razorpay/create-order",
        json={"order_id": online_order_id},
        headers={"Authorization": "Bearer token-a"},
    )
    assert res_rzp.status_code == 200
    assert res_rzp.get_json()["data"]["razorpay_order_id"].startswith("order_")


def test_invalid_payment_method_rejected(client, customer_user_a, cod_setup, monkeypatch):
    """TEST 11: Unsupported payment methods (e.g. 'cash', 'upi', 'razorpay_test') are rejected with 400."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post("/api/v1/cart", json={"product_id": cod_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})

    for invalid_method in ["cash", "upi", "razorpay_test", "crypto"]:
        res = client.post(
            "/api/v1/orders",
            json={"address_id": cod_setup["addr_a_id"], "payment_method": invalid_method},
            headers={"Authorization": "Bearer token-a"},
        )
        assert res.status_code == 400
        assert res.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_cod_other_user_address_rejected(client, customer_user_a, cod_setup, monkeypatch):
    """TEST 12: Customer cannot create COD order using another user's address."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post("/api/v1/cart", json={"product_id": cod_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})

    res = client.post(
        "/api/v1/orders",
        json={"address_id": cod_setup["addr_b_id"], "payment_method": "cod"},
        headers={"Authorization": "Bearer token-a"},
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_ADDRESS"


def test_out_of_stock_cod_rejected(client, app, customer_user_a, cod_setup, monkeypatch):
    """TEST 13: Out of stock COD order is rejected."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = cod_setup["p1_id"]
    client.post("/api/v1/cart", json={"product_id": p1_id, "quantity": 5}, headers={"Authorization": "Bearer token-a"})

    # Reduce product stock in DB below requested quantity
    with app.app_context():
        p = db.session.get(Product, p1_id)
        p.stock_quantity = 2
        db.session.commit()

    res = client.post(
        "/api/v1/orders",
        json={"address_id": cod_setup["addr_a_id"], "payment_method": "cod"},
        headers={"Authorization": "Bearer token-a"},
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_cod_cancellation_restores_stock_without_refund(client, app, customer_user_a, cod_setup, monkeypatch):
    """TEST 18, 19: COD order cancellation restores stock and leaves payment_status=pending without refunds."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = cod_setup["p1_id"]  # stock = 10

    client.post("/api/v1/cart", json={"product_id": p1_id, "quantity": 2}, headers={"Authorization": "Bearer token-a"})
    res_create = client.post("/api/v1/orders", json={"address_id": cod_setup["addr_a_id"], "payment_method": "cod"}, headers={"Authorization": "Bearer token-a"})
    order_id = res_create.get_json()["data"]["id"]

    # Cancel COD order
    res_cancel = client.post(f"/api/v1/orders/{order_id}/cancel", headers={"Authorization": "Bearer token-a"})
    assert res_cancel.status_code == 200
    data = res_cancel.get_json()["data"]

    assert data["order_status"] == "cancelled"
    assert data["payment_status"] == "pending"

    # Stock restored to 10
    with app.app_context():
        assert db.session.get(Product, p1_id).stock_quantity == 10


def test_razorpay_webhook_ignores_cod_payment(client, app, customer_user_a, cod_setup, monkeypatch):
    """TEST 20: Razorpay webhook does NOT affect or update COD orders."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post("/api/v1/cart", json={"product_id": cod_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})
    res_create = client.post("/api/v1/orders", json={"address_id": cod_setup["addr_a_id"], "payment_method": "cod"}, headers={"Authorization": "Bearer token-a"})
    cod_order_id = res_create.get_json()["data"]["id"]

    payload = {
        "event_id": "evt_cod_protection_020",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_fake_rzp", "order_id": f"ORD_MOCK_{cod_order_id}"}}},
    }
    body = json.dumps(payload).encode("utf-8")
    secret = app.config["RAZORPAY_WEBHOOK_SECRET"]
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    client.post("/api/v1/payments/razorpay/webhook", data=body, content_type="application/json", headers={"X-Razorpay-Signature": sig})

    # Assert COD order remains pending & provider='cod'
    with app.app_context():
        order = db.session.get(Order, cod_order_id)
        assert order.payment_status == "pending"
        assert order.payment_method == "cod"


def test_admin_cod_payment_confirmation_and_revenue_accounting(client, app, admin_user, customer_user_a, cod_setup, monkeypatch):
    """TEST 21, 22, 23: Admin confirms COD payment collection, and revenue metrics include paid COD while excluding pending COD."""
    # Create COD order as customer
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post("/api/v1/cart", json={"product_id": cod_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})
    res_create = client.post("/api/v1/orders", json={"address_id": cod_setup["addr_a_id"], "payment_method": "cod"}, headers={"Authorization": "Bearer token-a"})
    cod_order_id = res_create.get_json()["data"]["id"]

    # Switch to Admin
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    # 1. Update order status to confirmed
    client.patch(f"/api/v1/admin/orders/{cod_order_id}/status", json={"status": "confirmed"}, headers={"Authorization": "Bearer admin-token"})

    # 2. Dashboard revenue prior to COD payment collection should be 0.0 (unpaid pending COD is excluded)
    res_dash1 = client.get("/api/v1/admin/dashboard", headers={"Authorization": "Bearer admin-token"})
    assert res_dash1.get_json()["data"]["total_revenue"] == 0.0

    # 3. Confirm COD payment via Admin endpoint
    res_confirm = client.patch(f"/api/v1/admin/orders/{cod_order_id}/cod-payment", headers={"Authorization": "Bearer admin-token"})
    assert res_confirm.status_code == 200
    assert res_confirm.get_json()["data"]["payment_status"] == "paid"

    # 4. Dashboard revenue after COD collection should reflect order total (2000.0)
    res_dash2 = client.get("/api/v1/admin/dashboard", headers={"Authorization": "Bearer admin-token"})
    assert res_dash2.get_json()["data"]["total_revenue"] == 2000.0

