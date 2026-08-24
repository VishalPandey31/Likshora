import pytest
from app.models import (
    User, Address, CartItem, WishlistItem, Order, OrderItem,
    Payment, SearchHistory, Review, CustomerLoginLog, Product, Category
)
from app.extensions import db


@pytest.fixture
def test_setup(app):
    """Fixture providing setup data: categories, products, customers, and admin."""
    with app.app_context():
        # Create category & product
        cat = Category(name="Kurtis", slug="kurtis", description="Test category")
        db.session.add(cat)
        db.session.flush()

        prod = Product(
            sku="TEST-SKU-01",
            name="Test Kurti",
            slug="test-kurti",
            price=1999.00,
            stock_quantity=10,
            category_id=cat.id,
            is_active=True,
        )
        db.session.add(prod)

        # Create Customer A
        user_a = User(
            supabase_uid="supa-uuid-cust-a",
            name="Customer A",
            email="customer_a@example.com",
            phone="9876543210",
            role="customer",
            is_active=True,
            email_verified=True,
        )
        # Create Customer B
        user_b = User(
            supabase_uid="supa-uuid-cust-b",
            name="Customer B",
            email="customer_b@example.com",
            phone="9876543211",
            role="customer",
            is_active=True,
            email_verified=True,
        )
        # Create Admin
        admin_user = User(
            supabase_uid="supa-uuid-admin",
            name="Admin User",
            email="admin@example.com",
            phone="9876543212",
            role="admin",
            is_active=True,
            email_verified=True,
        )
        db.session.add_all([user_a, user_b, admin_user])
        db.session.commit()

        yield {
            "prod_id": prod.id,
            "user_a_id": user_a.id,
            "user_a_email": user_a.email,
            "user_a_uid": user_a.supabase_uid,
            "user_b_id": user_b.id,
            "user_b_email": user_b.email,
            "user_b_uid": user_b.supabase_uid,
            "admin_email": admin_user.email,
            "admin_uid": admin_user.supabase_uid,
        }


def test_supabase_uuid_linkage(client, test_setup):
    """Test that customer identity is correctly linked to Supabase Auth UUID."""
    user = User.query.filter_by(supabase_uid=test_setup["user_a_uid"]).first()
    assert user is not None
    assert user.email == test_setup["user_a_email"]
    assert user.supabase_uid == "supa-uuid-cust-a"


def test_customer_data_isolation(client, test_setup):
    """Test strict data isolation: Customer A cannot access Customer B's resources."""
    # Add address and cart item for Customer B
    addr_b = Address(
        user_id=test_setup["user_b_id"],
        full_name="Customer B",
        phone="9876543211",
        address_line1="House B",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400001",
        is_default=True,
    )
    cart_b = CartItem(user_id=test_setup["user_b_id"], product_id=test_setup["prod_id"], quantity=2)
    db.session.add_all([addr_b, cart_b])
    db.session.commit()

    # Log in as Customer A
    headers_a = {"Authorization": f"Bearer {test_setup['user_a_email']}"}

    # Customer A fetches cart
    res = client.get("/api/v1/cart", headers=headers_a)
    assert res.status_code == 200
    # Customer A should see empty cart
    assert res.json["data"]["item_count"] == 0

    # Customer A fetches addresses
    res = client.get("/api/v1/addresses", headers=headers_a)
    assert res.status_code == 200
    assert len(res.json["data"]) == 0


def test_search_history(client, test_setup):
    """Test recording, retrieving, and clearing search history for authenticated customer."""
    headers_a = {"Authorization": f"Bearer {test_setup['user_a_email']}"}

    # Perform product search
    client.get("/api/v1/products?search=kurti", headers=headers_a)

    # Retrieve search history
    res = client.get("/api/v1/search/history", headers=headers_a)
    assert res.status_code == 200
    assert len(res.json["data"]) >= 1
    assert res.json["data"][0]["query"] == "kurti"

    # Clear search history
    res = client.delete("/api/v1/search/history", headers=headers_a)
    assert res.status_code == 200

    # Verify cleared
    res = client.get("/api/v1/search/history", headers=headers_a)
    assert len(res.json["data"]) == 0


def test_review_submission_and_moderation(client, test_setup):
    """Test customer submitting review and admin moderating review."""
    headers_a = {"Authorization": f"Bearer {test_setup['user_a_email']}"}
    headers_admin = {"Authorization": f"Bearer dev-admin-token-{test_setup['admin_email']}"}

    # Customer submits review
    res = client.post(
        f"/api/v1/products/{test_setup['prod_id']}/reviews",
        json={"rating": 5, "comment": "Excellent quality!"},
        headers=headers_a,
    )
    assert res.status_code == 201
    rev_id = res.json["data"]["id"]
    assert res.json["data"]["status"] == "pending"

    # Public cannot see pending review
    res = client.get(f"/api/v1/products/{test_setup['prod_id']}/reviews")
    assert res.status_code == 200
    assert len(res.json["data"]["reviews"]) == 0

    # Admin approves review
    res = client.patch(
        f"/api/v1/admin/reviews/{rev_id}/status",
        json={"status": "approved"},
        headers=headers_admin,
    )
    assert res.status_code == 200

    # Public now sees approved review
    res = client.get(f"/api/v1/products/{test_setup['prod_id']}/reviews")
    assert res.status_code == 200
    assert len(res.json["data"]["reviews"]) == 1
    assert res.json["data"]["reviews"][0]["comment"] == "Excellent quality!"


def test_admin_customer_management(client, test_setup):
    """Test Admin endpoints for listing customers and inspecting full customer details & sub-resources."""
    headers_admin = {"Authorization": f"Bearer dev-admin-token-{test_setup['admin_email']}"}

    # Admin list customers
    res = client.get("/api/v1/admin/customers", headers=headers_admin)
    assert res.status_code == 200
    assert len(res.json["data"]) >= 2

    cust_a_id = test_setup["user_a_id"]

    # Admin inspect customer detail
    res = client.get(f"/api/v1/admin/customers/{cust_a_id}", headers=headers_admin)
    assert res.status_code == 200
    assert res.json["data"]["email"] == test_setup["user_a_email"]

    # Admin inspect sub-resources
    for sub in ["orders", "payments", "addresses", "cart", "wishlist", "search-history", "reviews", "login-logs"]:
        res = client.get(f"/api/v1/admin/customers/{cust_a_id}/{sub}", headers=headers_admin)
        assert res.status_code == 200, f"Failed on sub-resource: {sub}"

    # Admin toggle customer active status (block customer)
    res = client.patch(f"/api/v1/admin/customers/{cust_a_id}/status", json={"is_active": False}, headers=headers_admin)
    assert res.status_code == 200
    assert res.json["data"]["is_active"] is False

    # Blocked customer cannot login
    res = client.post("/api/v1/auth/login", json={"email": test_setup["user_a_email"], "password": "anypassword"})
    assert res.status_code in [401, 403]


def test_admin_authorization_enforcement(client, test_setup):
    """Test that non-admin customers are blocked from calling Admin APIs."""
    headers_cust = {"Authorization": f"Bearer {test_setup['user_a_email']}"}

    res = client.get("/api/v1/admin/customers", headers=headers_cust)
    assert res.status_code == 403
    assert res.json["error"]["code"] == "FORBIDDEN"


def test_no_passwords_or_secrets_exposed(client, test_setup):
    """Verify that customer profile and admin endpoints never expose password hashes or authentication secrets."""
    headers_admin = {"Authorization": f"Bearer dev-admin-token-{test_setup['admin_email']}"}

    res = client.get(f"/api/v1/admin/customers/{test_setup['user_a_id']}", headers=headers_admin)
    assert res.status_code == 200
    data = res.json["data"]

    assert "password" not in data
    assert "password_hash" not in data
    assert "secret" not in data
