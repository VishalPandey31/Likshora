from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from app.models import Order, OrderItem, Address, CartItem, Product, Category, Coupon, CouponUsage, User, Payment
from app.extensions import db


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-a-ord-uid",
            name="Customer A",
            email="customeraord@example.com",
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
            supabase_uid="test-customer-b-ord-uid",
            name="Customer B",
            email="customerbord@example.com",
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
            supabase_uid="test-admin-ord-uid",
            name="Admin User",
            email="adminord@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def checkout_setup(app, customer_user_a, customer_user_b):
    with app.app_context():
        cat = Category(name="Fashion", slug="fashion", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p1 = Product(
            category_id=cat.id,
            name="Denim Jacket",
            slug="denim-jacket",
            sku="JKT-DEN-001",
            price=2000.00,
            stock_quantity=10,
            is_active=True,
        )
        p2 = Product(
            category_id=cat.id,
            name="Sneakers",
            slug="sneakers",
            sku="SNK-002",
            price=1500.00,
            stock_quantity=5,
            is_active=True,
        )
        p_inactive = Product(
            category_id=cat.id,
            name="Disabled Shirt",
            slug="disabled-shirt",
            sku="SHT-DIS-003",
            price=500.00,
            stock_quantity=10,
            is_active=False,
        )
        db.session.add_all([p1, p2, p_inactive])
        db.session.commit()

        # Customer A Address
        addr_a = Address(
            user_id=customer_user_a["id"],
            full_name="Customer A",
            phone="9876543210",
            address_line1="100 Park Avenue",
            city="Delhi",
            state="Delhi",
            postal_code="110001",
            country="India",
            is_default=True,
        )
        # Customer B Address
        addr_b = Address(
            user_id=customer_user_b["id"],
            full_name="Customer B",
            phone="9999999999",
            address_line1="200 Sea Link",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400001",
            country="India",
            is_default=True,
        )
        db.session.add_all([addr_a, addr_b])
        db.session.commit()

        # Percentage Coupon
        c_pct = Coupon(
            code="SAVE10",
            discount_type="percentage",
            discount_value=10.00,
            minimum_order_amount=1000.00,
            per_user_limit=1,
            is_active=True,
        )
        # Expired Coupon
        c_exp = Coupon(
            code="EXPIRED",
            discount_type="fixed",
            discount_value=100.00,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True,
        )
        db.session.add_all([c_pct, c_exp])
        db.session.commit()

        return {
            "p1_id": p1.id,
            "p2_id": p2.id,
            "p_inactive_id": p_inactive.id,
            "addr_a_id": addr_a.id,
            "addr_b_id": addr_b.id,
            "c_pct_code": c_pct.code,
            "c_exp_code": c_exp.code,
        }


def test_create_order_success_cod(client, app, customer_user_a, checkout_setup, monkeypatch):
    """TEST 1: Create order with valid cart + valid address + COD."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = checkout_setup["p1_id"]
    addr_a_id = checkout_setup["addr_a_id"]

    # Add 2 items to cart (2000.0 * 2 = 4000.0)
    client.post(
        "/api/v1/cart",
        json={"product_id": p1_id, "quantity": 2},
        headers={"Authorization": "Bearer mock-token"},
    )

    response = client.post(
        "/api/v1/orders",
        json={"address_id": addr_a_id, "payment_method": "cod"},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]

    assert data["order_status"] == "pending"
    assert data["payment_status"] == "pending"
    assert data["payment_method"] == "cod"
    assert data["subtotal"] == 4000.0
    assert data["total_amount"] == 4000.0
    assert data["shipping_address"]["address_line1"] == "100 Park Avenue"
    assert len(data["items"]) == 1

    # Verify stock deducted (10 - 2 = 8) and cart cleared
    with app.app_context():
        product = db.session.get(Product, p1_id)
        assert product.stock_quantity == 8
        cart_count = CartItem.query.filter_by(user_id=customer_user_a["id"]).count()
        assert cart_count == 0


def test_create_order_online_payment_pending(client, app, customer_user_a, checkout_setup, monkeypatch):
    """TEST 2: Create order with online payment method has payment_status=pending without Razorpay calls."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = checkout_setup["p1_id"]
    addr_a_id = checkout_setup["addr_a_id"]

    client.post(
        "/api/v1/cart",
        json={"product_id": p1_id, "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )

    response = client.post(
        "/api/v1/orders",
        json={"address_id": addr_a_id, "payment_method": "online"},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["payment_method"] == "online"
    assert data["payment_status"] == "pending"


def test_create_order_empty_cart(client, customer_user_a, checkout_setup, monkeypatch):
    """TEST 3: Create order with empty cart returns 400 error."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    response = client.post(
        "/api/v1/orders",
        json={"address_id": checkout_setup["addr_a_id"], "payment_method": "cod"},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "EMPTY_CART"


def test_create_order_insufficient_stock(client, app, customer_user_a, checkout_setup, monkeypatch):
    """TEST 4: Insufficient stock rejects order, leaves stock unchanged and cart intact."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p2_id = checkout_setup["p2_id"]  # stock_quantity = 5

    client.post(
        "/api/v1/cart",
        json={"product_id": p2_id, "quantity": 3},
        headers={"Authorization": "Bearer mock-token"},
    )

    # Manually reduce stock in DB to 2 to simulate race condition
    with app.app_context():
        p2 = db.session.get(Product, p2_id)
        p2.stock_quantity = 2
        db.session.commit()

    response = client.post(
        "/api/v1/orders",
        json={"address_id": checkout_setup["addr_a_id"], "payment_method": "cod"},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INSUFFICIENT_STOCK"

    # Verify cart remains intact
    with app.app_context():
        cart_count = CartItem.query.filter_by(user_id=customer_user_a["id"]).count()
        assert cart_count == 1


def test_create_order_other_user_address(client, customer_user_a, checkout_setup, monkeypatch):
    """TEST 7: Address belonging to another user rejects order."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post(
        "/api/v1/cart",
        json={"product_id": checkout_setup["p1_id"], "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )

    response = client.post(
        "/api/v1/orders",
        json={"address_id": checkout_setup["addr_b_id"], "payment_method": "cod"},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_ADDRESS"


def test_create_order_with_valid_coupon(client, app, customer_user_a, checkout_setup, monkeypatch):
    """TEST 8: Order with valid percentage coupon calculates correct discount and creates coupon usage."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = checkout_setup["p1_id"]  # price 2000.0

    client.post(
        "/api/v1/cart",
        json={"product_id": p1_id, "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )

    response = client.post(
        "/api/v1/orders",
        json={
            "address_id": checkout_setup["addr_a_id"],
            "payment_method": "cod",
            "coupon_code": "SAVE10",
        },
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]

    assert data["subtotal"] == 2000.0
    assert data["discount_amount"] == 200.0  # 10% of 2000
    assert data["total_amount"] == 1800.0

    # Verify coupon usage created
    with app.app_context():
        usage_count = CouponUsage.query.filter_by(user_id=customer_user_a["id"]).count()
        assert usage_count == 1


def test_create_order_expired_coupon(client, customer_user_a, checkout_setup, monkeypatch):
    """TEST 9: Expired coupon rejects order."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post(
        "/api/v1/cart",
        json={"product_id": checkout_setup["p1_id"], "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )

    response = client.post(
        "/api/v1/orders",
        json={
            "address_id": checkout_setup["addr_a_id"],
            "payment_method": "cod",
            "coupon_code": "EXPIRED",
        },
        headers={"Authorization": "Bearer mock-token"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "COUPON_EXPIRED"


def test_get_user_orders_and_single_order_idor(client, app, customer_user_a, customer_user_b, checkout_setup, monkeypatch):
    """TEST 12, 13, 14: Customer can view their own order details, but User B cannot view User A's order."""
    # User A creates order
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post("/api/v1/cart", json={"product_id": checkout_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})
    res_create = client.post("/api/v1/orders", json={"address_id": checkout_setup["addr_a_id"], "payment_method": "cod"}, headers={"Authorization": "Bearer token-a"})
    order_a_id = res_create.get_json()["data"]["id"]

    # User A GET user orders
    res_list_a = client.get("/api/v1/orders", headers={"Authorization": "Bearer token-a"})
    assert res_list_a.status_code == 200
    assert len(res_list_a.get_json()["data"]) == 1

    # User B GET User A's order -> 404
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_b["supabase_uid"], "email": customer_user_b["email"]},
    )
    res_get_b = client.get(f"/api/v1/orders/{order_a_id}", headers={"Authorization": "Bearer token-b"})
    assert res_get_b.status_code == 404


def test_cancel_order_and_idempotent_stock_restoration(client, app, customer_user_a, checkout_setup, monkeypatch):
    """TEST 15, 18: Cancel pending order restores stock and is idempotent."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = checkout_setup["p1_id"]  # initial stock = 10

    client.post("/api/v1/cart", json={"product_id": p1_id, "quantity": 2}, headers={"Authorization": "Bearer token-a"})
    res_create = client.post("/api/v1/orders", json={"address_id": checkout_setup["addr_a_id"], "payment_method": "cod"}, headers={"Authorization": "Bearer token-a"})
    order_id = res_create.get_json()["data"]["id"]

    # Stock should be 8 now
    with app.app_context():
        assert db.session.get(Product, p1_id).stock_quantity == 8

    # Cancel order
    res_cancel = client.post(f"/api/v1/orders/{order_id}/cancel", headers={"Authorization": "Bearer token-a"})
    assert res_cancel.status_code == 200
    assert res_cancel.get_json()["data"]["order_status"] == "cancelled"

    # Stock restored to 10
    with app.app_context():
        assert db.session.get(Product, p1_id).stock_quantity == 10

    # Repeat cancel request (idempotent test)
    res_cancel2 = client.post(f"/api/v1/orders/{order_id}/cancel", headers={"Authorization": "Bearer token-a"})
    assert res_cancel2.status_code == 400
    assert res_cancel2.get_json()["error"]["code"] == "CANNOT_CANCEL"

    # Stock remains 10 without double restoration
    with app.app_context():
        assert db.session.get(Product, p1_id).stock_quantity == 10


def test_admin_order_status_transitions(client, app, admin_user, customer_user_a, checkout_setup, monkeypatch):
    """TEST 19-24: Admin state machine transitions and invalid transition rejection."""
    # Create order as Customer A
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    client.post("/api/v1/cart", json={"product_id": checkout_setup["p1_id"], "quantity": 1}, headers={"Authorization": "Bearer token-a"})
    res_create = client.post("/api/v1/orders", json={"address_id": checkout_setup["addr_a_id"], "payment_method": "cod"}, headers={"Authorization": "Bearer token-a"})
    order_id = res_create.get_json()["data"]["id"]

    # Customer attempts admin status update -> 403
    res_cust_update = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "confirmed"}, headers={"Authorization": "Bearer token-a"})
    assert res_cust_update.status_code == 403

    # Switch to Admin
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    # Invalid jump: pending -> delivered -> 400
    res_invalid = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "delivered"}, headers={"Authorization": "Bearer admin-token"})
    assert res_invalid.status_code == 400
    assert res_invalid.get_json()["error"]["code"] == "INVALID_STATUS_TRANSITION"

    # Valid transitions: processing -> shipped -> delivered
    assert client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "processing"}, headers={"Authorization": "Bearer admin-token"}).status_code == 200
    assert client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "shipped"}, headers={"Authorization": "Bearer admin-token"}).status_code == 200

    res_deliv = client.patch(f"/api/v1/admin/orders/{order_id}/status", json={"status": "delivered"}, headers={"Authorization": "Bearer admin-token"})
    assert res_deliv.status_code == 200
    assert res_deliv.get_json()["data"]["order_status"] == "delivered"
    assert res_deliv.get_json()["data"]["payment_status"] == "paid"  # COD delivered auto-sets paid
