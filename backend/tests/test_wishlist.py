import pytest
from app.models import WishlistItem, CartItem, Product, Category, User
from app.extensions import db


@pytest.fixture
def customer_user_a(app):
    with app.app_context():
        user = User(
            supabase_uid="test-customer-a-wish-uid",
            name="Customer A",
            email="customerawish@example.com",
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
            supabase_uid="test-customer-b-wish-uid",
            name="Customer B",
            email="customerbwish@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "supabase_uid": user.supabase_uid, "email": user.email}


@pytest.fixture
def wishlist_products(app):
    with app.app_context():
        cat = Category(name="Accessories", slug="accessories", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p1 = Product(
            category_id=cat.id,
            name="Leather Wallet",
            slug="leather-wallet",
            sku="WLT-001",
            price=1299.00,
            stock_quantity=15,
            is_active=True,
        )
        p_out = Product(
            category_id=cat.id,
            name="Sold Out Belt",
            slug="sold-out-belt",
            sku="BLT-002",
            price=799.00,
            stock_quantity=0,
            is_active=True,
        )
        db.session.add_all([p1, p_out])
        db.session.commit()

        return {"p1_id": p1.id, "p_out_id": p_out.id}


def test_unauthenticated_wishlist_returns_401(client):
    """Test wishlist endpoints return 401 when no token is provided."""
    assert client.get("/api/v1/wishlist").status_code == 401
    assert client.post("/api/v1/wishlist", json={"product_id": 1}).status_code == 401


def test_add_to_wishlist_and_prevent_duplicate(client, app, customer_user_a, wishlist_products, monkeypatch):
    """Test adding to wishlist and handling duplicate addition cleanly."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = wishlist_products["p1_id"]

    # First addition
    res1 = client.post(
        "/api/v1/wishlist",
        json={"product_id": p1_id},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res1.status_code == 201
    item_id = res1.get_json()["data"]["id"]

    # Duplicate addition
    res2 = client.post(
        "/api/v1/wishlist",
        json={"product_id": p1_id},
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res2.status_code == 200
    assert res2.get_json()["message"] == "Product is already in your wishlist"

    # Verify only 1 wishlist row exists in database
    with app.app_context():
        count = WishlistItem.query.filter_by(user_id=customer_user_a["id"]).count()
        assert count == 1


def test_check_wishlist_status(client, app, customer_user_a, wishlist_products, monkeypatch):
    """Test GET /api/v1/wishlist/check/<product_id> returns wishlisted state."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = wishlist_products["p1_id"]
    p_out_id = wishlist_products["p_out_id"]

    # Check non-wishlisted product
    res_before = client.get(
        f"/api/v1/wishlist/check/{p1_id}",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_before.status_code == 200
    assert res_before.get_json()["data"]["is_wishlisted"] is False

    # Add p1_id to wishlist
    client.post(
        "/api/v1/wishlist",
        json={"product_id": p1_id},
        headers={"Authorization": "Bearer mock-token"},
    )

    # Check wishlisted product
    res_after = client.get(
        f"/api/v1/wishlist/check/{p1_id}",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_after.status_code == 200
    assert res_after.get_json()["data"]["is_wishlisted"] is True


def test_delete_wishlist_item(client, app, customer_user_a, wishlist_products, monkeypatch):
    """Test removing item from wishlist."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )

    res_add = client.post(
        "/api/v1/wishlist",
        json={"product_id": wishlist_products["p1_id"]},
        headers={"Authorization": "Bearer mock-token"},
    )
    item_id = res_add.get_json()["data"]["id"]

    res_del = client.delete(
        f"/api/v1/wishlist/{item_id}",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_del.status_code == 200

    res_get = client.get("/api/v1/wishlist", headers={"Authorization": "Bearer mock-token"})
    assert res_get.get_json()["item_count"] == 0


def test_move_wishlist_to_cart_success(client, app, customer_user_a, wishlist_products, monkeypatch):
    """Test moving item from wishlist to cart atomically."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p1_id = wishlist_products["p1_id"]

    res_add = client.post(
        "/api/v1/wishlist",
        json={"product_id": p1_id},
        headers={"Authorization": "Bearer mock-token"},
    )
    item_id = res_add.get_json()["data"]["id"]

    res_move = client.post(
        f"/api/v1/wishlist/{item_id}/move-to-cart",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_move.status_code == 200
    assert res_move.get_json()["success"] is True

    # Verify wishlist item is deleted and cart item is created
    with app.app_context():
        wish_count = WishlistItem.query.filter_by(user_id=customer_user_a["id"]).count()
        cart_item = CartItem.query.filter_by(user_id=customer_user_a["id"], product_id=p1_id).first()
        assert wish_count == 0
        assert cart_item is not None
        assert cart_item.quantity == 1


def test_move_out_of_stock_wishlist_item_fails_and_preserves_item(client, app, customer_user_a, wishlist_products, monkeypatch):
    """Test moving an out-of-stock wishlist item fails and preserves the wishlist item."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    p_out_id = wishlist_products["p_out_id"]

    res_add = client.post(
        "/api/v1/wishlist",
        json={"product_id": p_out_id},
        headers={"Authorization": "Bearer mock-token"},
    )
    item_id = res_add.get_json()["data"]["id"]

    res_move = client.post(
        f"/api/v1/wishlist/{item_id}/move-to-cart",
        headers={"Authorization": "Bearer mock-token"},
    )
    assert res_move.status_code == 400
    assert res_move.get_json()["error"]["code"] == "INSUFFICIENT_STOCK"

    # Verify wishlist item was preserved
    with app.app_context():
        wish_count = WishlistItem.query.filter_by(user_id=customer_user_a["id"]).count()
        assert wish_count == 1


def test_idor_protection_wishlist(client, app, customer_user_a, customer_user_b, wishlist_products, monkeypatch):
    """Test User B cannot delete or move User A's wishlist item (IDOR protection)."""
    # User A adds item
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_a["supabase_uid"], "email": customer_user_a["email"]},
    )
    res_add = client.post(
        "/api/v1/wishlist",
        json={"product_id": wishlist_products["p1_id"]},
        headers={"Authorization": "Bearer user-a-token"},
    )
    user_a_wish_id = res_add.get_json()["data"]["id"]

    # User B attempts delete
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user_b["supabase_uid"], "email": customer_user_b["email"]},
    )
    res_b_del = client.delete(
        f"/api/v1/wishlist/{user_a_wish_id}",
        headers={"Authorization": "Bearer user-b-token"},
    )
    assert res_b_del.status_code == 404

    # User B attempts move to cart
    res_b_move = client.post(
        f"/api/v1/wishlist/{user_a_wish_id}/move-to-cart",
        headers={"Authorization": "Bearer user-b-token"},
    )
    assert res_b_move.status_code == 404
