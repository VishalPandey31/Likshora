import pytest
from app.models import Order, OrderItem, Product, Category, User, Address, Payment
from app.extensions import db


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User(
            supabase_uid="test-admin-dash-uid",
            name="Admin Operator",
            email="admindash@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def customer_user(app):
    with app.app_context():
        cust = User(
            supabase_uid="test-cust-dash-uid",
            name="Customer Alice",
            email="alice@example.com",
            phone="9876543210",
            role="customer",
            is_active=True,
        )
        db.session.add(cust)
        db.session.commit()
        return {"id": cust.id, "supabase_uid": cust.supabase_uid, "email": cust.email}


@pytest.fixture
def admin_test_data(app, customer_user):
    with app.app_context():
        cat = Category(name="Apparel", slug="apparel", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p_normal = Product(
            category_id=cat.id,
            name="Normal Stock Shirt",
            slug="normal-stock-shirt",
            sku="SHT-NORM-01",
            price=1000.00,
            stock_quantity=50,
            is_active=True,
        )
        p_low = Product(
            category_id=cat.id,
            name="Low Stock Jeans",
            slug="low-stock-jeans",
            sku="JNS-LOW-02",
            price=2500.00,
            stock_quantity=3,
            is_active=True,
        )
        p_out = Product(
            category_id=cat.id,
            name="Out of Stock Belt",
            slug="out-of-stock-belt",
            sku="BLT-OUT-03",
            price=500.00,
            stock_quantity=0,
            is_active=True,
        )
        db.session.add_all([p_normal, p_low, p_out])
        db.session.commit()

        addr = Address(
            user_id=customer_user["id"],
            full_name="Customer Alice",
            phone="9876543210",
            address_line1="123 High Street",
            city="Bangalore",
            state="Karnataka",
            postal_code="560001",
            country="India",
            is_default=True,
        )
        db.session.add(addr)
        db.session.commit()

        # Order 1: Confirmed (Revenue = 2500.0)
        o1 = Order(
            user_id=customer_user["id"],
            address_id=addr.id,
            order_number="ORD-2026-0001",
            subtotal=2500.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=2500.00,
            payment_method="cod",
            payment_status="paid",
            order_status="confirmed",
            shipping_full_name=addr.full_name,
            shipping_phone=addr.phone,
            shipping_address_line1=addr.address_line1,
            shipping_city=addr.city,
            shipping_state=addr.state,
            shipping_postal_code=addr.postal_code,
            shipping_country=addr.country,
        )
        # Order 2: Pending
        o2 = Order(
            user_id=customer_user["id"],
            address_id=addr.id,
            order_number="ORD-2026-0002",
            subtotal=1000.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=1000.00,
            payment_method="online",
            payment_status="pending",
            order_status="pending",
            shipping_full_name=addr.full_name,
            shipping_phone=addr.phone,
            shipping_address_line1=addr.address_line1,
            shipping_city=addr.city,
            shipping_state=addr.state,
            shipping_postal_code=addr.postal_code,
            shipping_country=addr.country,
        )
        # Order 3: Cancelled (Excluded from Revenue)
        o3 = Order(
            user_id=customer_user["id"],
            address_id=addr.id,
            order_number="ORD-2026-0003",
            subtotal=500.00,
            discount_amount=0.00,
            shipping_amount=0.00,
            total_amount=500.00,
            payment_method="cod",
            payment_status="pending",
            order_status="cancelled",
            shipping_full_name=addr.full_name,
            shipping_phone=addr.phone,
            shipping_address_line1=addr.address_line1,
            shipping_city=addr.city,
            shipping_state=addr.state,
            shipping_postal_code=addr.postal_code,
            shipping_country=addr.country,
        )
        db.session.add_all([o1, o2, o3])
        db.session.commit()

        # Order Items
        item1 = OrderItem(order_id=o1.id, product_id=p_low.id, product_name=p_low.name, sku=p_low.sku, quantity=1, unit_price=2500.00, subtotal=2500.00)
        item2 = OrderItem(order_id=o2.id, product_id=p_normal.id, product_name=p_normal.name, sku=p_normal.sku, quantity=1, unit_price=1000.00, subtotal=1000.00)
        item3 = OrderItem(order_id=o3.id, product_id=p_out.id, product_name=p_out.name, sku=p_out.sku, quantity=1, unit_price=500.00, subtotal=500.00)
        db.session.add_all([item1, item2, item3])

        pay1 = Payment(order_id=o1.id, payment_method="cod", provider="cod", amount=2500.00, currency="INR", status="captured")
        db.session.add(pay1)
        db.session.commit()

        return {
            "p_low_id": p_low.id,
            "o1_id": o1.id,
            "o2_id": o2.id,
        }


def test_admin_dashboard_metrics(client, admin_user, admin_test_data, monkeypatch):
    """Test GET /api/v1/admin/dashboard calculates accurate metrics using DB aggregation."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    response = client.get("/api/v1/admin/dashboard", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["total_orders"] == 3
    assert data["total_revenue"] == 2500.0  # Confirmed order total only (cancelled excluded)
    assert data["total_customers"] == 1    # Customer Alice only (admin excluded)
    assert data["total_products"] == 3
    assert data["low_stock_products"] == 1 # Low Stock Jeans (stock 3 <= 5)
    assert data["pending_orders"] == 1    # Order 2 pending


def test_admin_low_stock_products(client, admin_user, admin_test_data, monkeypatch):
    """Test GET /api/v1/admin/products/low-stock returns inventory alerts."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    response = client.get("/api/v1/admin/products/low-stock", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 200
    res = response.get_json()
    assert res["count"] == 1
    assert res["data"][0]["sku"] == "JNS-LOW-02"


def test_admin_orders_list_search_and_filter(client, admin_user, admin_test_data, monkeypatch):
    """Test GET /api/v1/admin/orders filtering by status and searching."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    # Status filter
    res_pending = client.get("/api/v1/admin/orders?status=pending", headers={"Authorization": "Bearer admin-token"})
    assert res_pending.status_code == 200
    assert len(res_pending.get_json()["data"]) == 1
    assert res_pending.get_json()["data"][0]["order_number"] == "ORD-2026-0002"

    # Search by order number
    res_search = client.get("/api/v1/admin/orders?search=ORD-2026-0001", headers={"Authorization": "Bearer admin-token"})
    assert res_search.status_code == 200
    assert len(res_search.get_json()["data"]) == 1


def test_admin_order_detail(client, admin_user, admin_test_data, monkeypatch):
    """Test GET /api/v1/admin/orders/<id> includes customer snapshot, items, and payments."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    o1_id = admin_test_data["o1_id"]
    response = client.get(f"/api/v1/admin/orders/{o1_id}", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 200
    data = response.get_json()["data"]

    assert data["order_number"] == "ORD-2026-0001"
    assert data["customer"]["email"] == "alice@example.com"
    assert len(data["items"]) == 1
    assert len(data["payments"]) == 1


def test_admin_customers_list_and_detail(client, admin_user, customer_user, admin_test_data, monkeypatch):
    """Test GET /api/v1/admin/customers and GET /api/v1/admin/customers/<id>."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    # Customer List
    res_list = client.get("/api/v1/admin/customers", headers={"Authorization": "Bearer admin-token"})
    assert res_list.status_code == 200
    custs = res_list.get_json()["data"]
    assert len(custs) == 1
    assert custs[0]["email"] == "alice@example.com"
    assert custs[0]["total_spent"] == 2500.0
    assert "password" not in custs[0]

    # Customer Detail
    c_id = customer_user["id"]
    res_detail = client.get(f"/api/v1/admin/customers/{c_id}", headers={"Authorization": "Bearer admin-token"})
    assert res_detail.status_code == 200
    d_data = res_detail.get_json()["data"]
    assert d_data["email"] == "alice@example.com"
    assert len(d_data["addresses"]) == 1
    assert len(d_data["recent_orders"]) == 3


def test_admin_customer_orders_history(client, admin_user, customer_user, admin_test_data, monkeypatch):
    """Test GET /api/v1/admin/customers/<id>/orders."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )
    c_id = customer_user["id"]
    response = client.get(f"/api/v1/admin/customers/{c_id}/orders", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 3


def test_admin_endpoints_rbac_customer_denial(client, customer_user, admin_test_data, monkeypatch):
    """Test all admin endpoints return 403 Forbidden when called by a customer."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user["supabase_uid"], "email": customer_user["email"]},
    )
    o1_id = admin_test_data["o1_id"]
    c_id = customer_user["id"]

    assert client.get("/api/v1/admin/dashboard", headers={"Authorization": "Bearer cust-token"}).status_code == 403
    assert client.get("/api/v1/admin/products/low-stock", headers={"Authorization": "Bearer cust-token"}).status_code == 403
    assert client.get("/api/v1/admin/orders", headers={"Authorization": "Bearer cust-token"}).status_code == 403
    assert client.get(f"/api/v1/admin/orders/{o1_id}", headers={"Authorization": "Bearer cust-token"}).status_code == 403
    assert client.get("/api/v1/admin/customers", headers={"Authorization": "Bearer cust-token"}).status_code == 403
    assert client.get(f"/api/v1/admin/customers/{c_id}", headers={"Authorization": "Bearer cust-token"}).status_code == 403
    assert client.get(f"/api/v1/admin/customers/{c_id}/orders", headers={"Authorization": "Bearer cust-token"}).status_code == 403


def test_admin_endpoints_unauthenticated_returns_401(client, admin_test_data):
    """Test all admin endpoints return 401 Unauthorized without Bearer token."""
    assert client.get("/api/v1/admin/dashboard").status_code == 401
    assert client.get("/api/v1/admin/products/low-stock").status_code == 401
    assert client.get("/api/v1/admin/orders").status_code == 401
    assert client.get("/api/v1/admin/customers").status_code == 401
