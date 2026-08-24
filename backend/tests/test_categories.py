import pytest
from app.models import Category, User, Product
from app.extensions import db


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User(
            supabase_uid="test-admin-cat-uid",
            name="Admin User",
            email="admincat@example.com",
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": admin.id, "supabase_uid": admin.supabase_uid, "email": admin.email}


@pytest.fixture
def customer_user(app):
    with app.app_context():
        customer = User(
            supabase_uid="test-customer-cat-uid",
            name="Customer User",
            email="customercat@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(customer)
        db.session.commit()
        return {"id": customer.id, "supabase_uid": customer.supabase_uid, "email": customer.email}


def test_get_categories_list(client, app):
    """Test GET /api/v1/categories returns active categories."""
    with app.app_context():
        c1 = Category(name="Men", slug="men", is_active=True)
        c2 = Category(name="Women", slug="women", is_active=True)
        c3 = Category(name="Drafts", slug="drafts", is_active=False)
        db.session.add_all([c1, c2, c3])
        db.session.commit()

    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    slugs = [cat["slug"] for cat in data["data"]]
    assert "men" in slugs
    assert "women" in slugs
    assert "drafts" not in slugs


def test_get_category_detail(client, app):
    """Test GET /api/v1/categories/<slug> returns category and products."""
    with app.app_context():
        cat = Category(name="T-Shirts", slug="t-shirts", is_active=True)
        db.session.add(cat)
        db.session.commit()

        p = Product(
            category_id=cat.id,
            name="Graphic Tee",
            slug="graphic-tee",
            sku="TEE-001",
            price=599.00,
            stock_quantity=10,
            is_active=True,
        )
        db.session.add(p)
        db.session.commit()

    response = client.get("/api/v1/categories/t-shirts")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["category"]["slug"] == "t-shirts"
    assert len(data["data"]["products"]) == 1
    assert data["data"]["products"][0]["sku"] == "TEE-001"


def test_create_category_admin(client, app, admin_user, monkeypatch):
    """Test POST /api/v1/categories creates category with admin token."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    response = client.post(
        "/api/v1/categories",
        json={"name": "Accessories", "description": "Bags and belts"},
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["slug"] == "accessories"


def test_create_category_customer_denied(client, app, customer_user, monkeypatch):
    """Test POST /api/v1/categories returns 403 for customer token."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": customer_user["supabase_uid"], "email": customer_user["email"]},
    )

    response = client.post(
        "/api/v1/categories",
        json={"name": "Forbidden Category"},
        headers={"Authorization": "Bearer mock-customer-token"},
    )
    assert response.status_code == 403


def test_update_category_admin(client, app, admin_user, monkeypatch):
    """Test PUT /api/v1/categories/<id> updates category."""
    with app.app_context():
        cat = Category(name="Jackets", slug="jackets", is_active=True)
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id

    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    response = client.put(
        f"/api/v1/categories/{cat_id}",
        json={"name": "Winter Jackets", "description": "Coats and parkas"},
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["data"]["name"] == "Winter Jackets"


def test_delete_category_admin(client, app, admin_user, monkeypatch):
    """Test DELETE /api/v1/categories/<id> soft-deactivates category."""
    with app.app_context():
        cat = Category(name="Seasonal", slug="seasonal", is_active=True)
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id

    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    response = client.delete(
        f"/api/v1/categories/{cat_id}",
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert response.status_code == 200

    with app.app_context():
        updated_cat = db.session.get(Category, cat_id)
        assert updated_cat.is_active is False
