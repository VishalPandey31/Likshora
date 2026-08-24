import pytest
from app.models import CartItem, Product, Category, User
from app.extensions import db


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-a-cart-uid",
            name="Customer A",
            email="customera@example.com",
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
            supabase_uid="test-customer-b-cart-uid",
            name="Customer B",
            email="customerb@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def cart_products(app):
    with app.app_context():
        cat = Category(name="Apparel", slug="apparel", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p1 = Product(
            category_id=cat.id,
            name="Classic T-Shirt",
            slug="classic-tshirt",
            sku="TSH-001",
            price=999.00,
            stock_quantity=10,
            is_active=True,
        )
        p2 = Product(
            category_id=cat.id,
            name="Hoodie",
            slug="hoodie",
            sku="HD-002",
            price=1999.00,
            stock_quantity=5,
            is_active=True,
        )
        p_out = Product(
            category_id=cat.id,
            name="Sold Out Jacket",
            slug="sold-out-jacket",
            sku="JKT-003",
            price=2999.00,
            stock_quantity=0,
            is_active=True,
        )
        p_inactive = Product(
            category_id=cat.id,
            name="Archived Shirt",
            slug="archived-shirt",
            sku="SHT-004",
            price=499.00,
            stock_quantity=20,
            is_active=False,
        )
        db.session.add_all([p1, p2, p_out, p_inactive])
        db.session.commit()

        return {"p1_id": p1.id, "p2_id": p2.id, "p_out_id": p_out.id, "p_inactive_id": p_inactive.id}


def test_unauthenticated_cart_returns_401(client):
    """Test cart endpoints return 401 when no token is provided."""
    assert client.get("/api/v1/cart").status_code == 401
    assert client.post("/api/v1/cart", json={"product_id": 1}).status_code == 401


def test_get_empty_cart(client, app, customer_user_a, monkeypatch):
    """Test GET /api/v1/cart for a new user returns empty cart state."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    response = client.get("/api/v1/cart", headers={"Authorization": "Bearer mock-token"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["items"] == []
    assert data["data"]["subtotal"] == 0.0
    assert data["data"]["total"] == 0.0
    assert data["data"]["item_count"] == 0


def test_add_to_cart_and_increment(client, app, customer_user_a, cart_products, monkeypatch):
    """Test adding item to cart and adding same item again increments quantity."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = cart_products["p1_id"]

    # First addition (qty=2)
    res1 = client.post(
        "/api/v1/cart",
        json={"product_id": p1_id, "quantity": 2},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res1.status_code == 201
    assert res1.get_json()["data"]["quantity"] == 2

    # Second addition (qty=3)
    res2 = client.post(
        "/api/v1/cart",
        json={"product_id": p1_id, "quantity": 3},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res2.status_code == 200
    assert res2.get_json()["data"]["quantity"] == 5

    # Verify no stock was deducted from database
    with app.app_context():
        product = db.session.get(Product, p1_id)
        assert product.stock_quantity == 10

    # Verify cart subtotal
    res_get = client.get("/api/v1/cart", headers={"Authorization": "Bearer mock-token"})
    assert res_get.get_json()["data"]["subtotal"] == 4995.0  # 999.0 * 5


def test_add_out_of_stock_and_inactive_product(client, app, customer_user_a, cart_products, monkeypatch):
    """Test adding out-of-stock or inactive products returns proper 400 errors."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    # Out of stock
    res_out = client.post(
        "/api/v1/cart",
        json={"product_id": cart_products["p_out_id"], "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_out.status_code == 400
    assert res_out.get_json()["error"]["code"] == "INSUFFICIENT_STOCK"

    # Inactive
    res_inact = client.post(
        "/api/v1/cart",
        json={"product_id": cart_products["p_inactive_id"], "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_inact.status_code == 400
    assert res_inact.get_json()["error"]["code"] == "PRODUCT_INACTIVE"


def test_update_cart_quantity_and_stock_limit(client, app, customer_user_a, cart_products, monkeypatch):
    """Test updating cart quantity and stock limit validation."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p2_id = cart_products["p2_id"]  # stock_quantity = 5

    res_add = client.post(
        "/api/v1/cart",
        json={"product_id": p2_id, "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )
    cart_item_id = res_add.get_json()["data"]["id"]

    # Valid update (qty=4)
    res_up = client.put(
        f"/api/v1/cart/{cart_item_id}",
        json={"quantity": 4},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_up.status_code == 200
    assert res_up.get_json()["data"]["quantity"] == 4

    # Invalid update exceeding stock (qty=10 > stock 5)
    res_exceed = client.put(
        f"/api/v1/cart/{cart_item_id}",
        json={"quantity": 10},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_exceed.status_code == 400
    assert res_exceed.get_json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_delete_and_clear_cart(client, app, customer_user_a, cart_products, monkeypatch):
    """Test deleting single cart item and clearing cart."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    res_add1 = client.post(
        "/api/v1/cart",
        json={"product_id": cart_products["p1_id"], "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )
    cart_item1_id = res_add1.get_json()["data"]["id"]

    client.post(
        "/api/v1/cart",
        json={"product_id": cart_products["p2_id"], "quantity": 1},
        headers={"Authorization": "Bearer mock-token"},
    )

    # Delete item 1
    res_del1 = client.delete(
        f"/api/v1/cart/{cart_item1_id}",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_del1.status_code == 200

    # Clear remaining cart
    res_clear = client.delete("/api/v1/cart", headers={"Authorization": "Bearer mock-token"})
    assert res_clear.status_code == 200
    assert res_clear.get_json()["data"]["items"] == []


def test_idor_protection_cart(client, app, customer_user_a, customer_user_b, cart_products, monkeypatch):
    """Test User B cannot update or delete User A's cart item (IDOR protection)."""
    # User A adds item
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_add = client.post(
        "/api/v1/cart",
        json={"product_id": cart_products["p1_id"], "quantity": 1},
        headers={"Authorization": "Bearer user-a-token"},
    )
    user_a_cart_item_id = res_add.get_json()["data"]["id"]

    # User B attempts to update User A's cart item
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_b["supabase_uid"], "email": customer_user_b["email"]},
    )
    res_b_update = client.put(
        f"/api/v1/cart/{user_a_cart_item_id}",
        json={"quantity": 5},
        headers={"Authorization": "Bearer user-b-token"},
    )
    assert res_b_update.status_code == 404

    # User B attempts to delete User A's cart item
    res_b_delete = client.delete(
        f"/api/v1/cart/{user_a_cart_item_id}",
        headers={"Authorization": "Bearer user-b-token"},
    )
    assert res_b_delete.status_code == 404
