import pytest
from app.models import Product, Category, ProductImage, User
from app.extensions import db


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User(
            supabase_uid="test-admin-prod-uid",
            name="Admin User",
            email="adminprod@example.com",
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
            supabase_uid="test-customer-prod-uid",
            name="Customer User",
            email="customerprod@example.com",
            role="customer",
            is_active=True,
        )
        db.session.add(customer)
        db.session.commit()
        return {"id": customer.id, "supabase_uid": customer.supabase_uid, "email": customer.email}


@pytest.fixture
def sample_catalog(app):
    with app.app_context():
        c_men = Category(name="Men Apparel", slug="men", is_active=True)
        c_women = Category(name="Women Apparel", slug="women", is_active=True)
        db.session.add_all([c_men, c_women])
        db.session.commit()

        p1 = Product(
            category_id=c_men.id,
            name="Slim Fit Denim Jeans",
            slug="slim-fit-denim-jeans",
            sku="JNS-MEN-001",
            price=1499.00,
            compare_at_price=1999.00,
            stock_quantity=25,
            is_active=True,
            is_featured=True,
            is_trending=False,
        )
        p2 = Product(
            category_id=c_men.id,
            name="Casual Cotton Shirt",
            slug="casual-cotton-shirt",
            sku="SHT-MEN-002",
            price=899.00,
            stock_quantity=15,
            is_active=True,
            is_featured=False,
            is_trending=True,
        )
        p3 = Product(
            category_id=c_women.id,
            name="Floral Summer Dress",
            slug="floral-summer-dress",
            sku="DRS-WMN-003",
            price=2499.00,
            stock_quantity=0,
            is_active=True,
            is_featured=True,
            is_trending=True,
        )
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        img1 = ProductImage(product_id=p1.id, image_url="https://img.com/jns1.jpg", is_primary=True)
        img2 = ProductImage(product_id=p1.id, image_url="https://img.com/jns2.jpg", is_primary=False)
        db.session.add_all([img1, img2])
        db.session.commit()


def test_get_products_list_pagination(client, sample_catalog):
    """Test public GET /api/v1/products returns paginated products."""
    response = client.get("/api/v1/products?page=1&per_page=2")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["total_pages"] == 2


def test_search_products(client, sample_catalog):
    """Test searching products by query term."""
    response = client.get("/api/v1/products?search=shirt")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["data"]) == 1
    assert data["data"][0]["sku"] == "SHT-MEN-002"


def test_filter_by_category(client, sample_catalog):
    """Test filtering products by category slug."""
    response = client.get("/api/v1/products?category=men")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["data"]) == 2


def test_filter_by_price_range(client, sample_catalog):
    """Test price range filtering min_price and max_price."""
    response = client.get("/api/v1/products?min_price=1000&max_price=2000")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["data"]) == 1
    assert data["data"][0]["sku"] == "JNS-MEN-001"


def test_invalid_price_range_error(client, sample_catalog):
    """Test min_price > max_price returns 400 validation error."""
    response = client.get("/api/v1/products?min_price=3000&max_price=1000")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "INVALID_PRICE_RANGE"


def test_filter_featured_and_trending(client, sample_catalog):
    """Test featured=true and trending=true query filters."""
    res_featured = client.get("/api/v1/products?featured=true")
    assert res_featured.status_code == 200
    assert len(res_featured.get_json()["data"]) == 2

    res_trending = client.get("/api/v1/products?trending=true")
    assert res_trending.status_code == 200
    assert len(res_trending.get_json()["data"]) == 2


def test_sorting_products(client, sample_catalog):
    """Test sorting products by price low to high."""
    response = client.get("/api/v1/products?sort=price_low_to_high")
    assert response.status_code == 200
    prices = [p["price"] for p in response.get_json()["data"]]
    assert prices == sorted(prices)


def test_get_product_detail(client, sample_catalog):
    """Test GET /api/v1/products/<slug> returns full product details and images."""
    response = client.get("/api/v1/products/slim-fit-denim-jeans")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["sku"] == "JNS-MEN-001"
    assert data["data"]["in_stock"] is True
    assert len(data["data"]["images"]) == 2


def test_admin_create_product(client, app, admin_user, sample_catalog, monkeypatch):
    """Test POST /api/v1/products creates product with admin token."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Linen Trousers",
            "sku": "TRS-MEN-004",
            "price": 1799.00,
            "stock_quantity": 20,
            "is_featured": True,
            "is_trending": True,
        },
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["sku"] == "TRS-MEN-004"
    assert data["data"]["is_trending"] is True


def test_admin_create_product_duplicate_sku(client, app, admin_user, sample_catalog, monkeypatch):
    """Test duplicate SKU returns 409 conflict error."""
    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Duplicate SKU Product",
            "sku": "JNS-MEN-001",
            "price": 1000.00,
        },
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "SKU_EXISTS"


def test_admin_update_stock(client, app, admin_user, sample_catalog, monkeypatch):
    """Test PATCH /api/v1/products/<id>/stock updates inventory stock."""
    with app.app_context():
        prod = Product.query.filter_by(sku="JNS-MEN-001").first()
        prod_id = prod.id

    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    response = client.patch(
        f"/api/v1/products/{prod_id}/stock",
        json={"stock_quantity": 100},
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["data"]["stock_quantity"] == 100
    assert data["data"]["in_stock"] is True


def test_admin_add_and_delete_product_image(client, app, admin_user, sample_catalog, monkeypatch):
    """Test adding and deleting gallery images for a product."""
    with app.app_context():
        prod = Product.query.filter_by(sku="SHT-MEN-002").first()
        prod_id = prod.id

    monkeypatch.setattr(
        "app.auth.decorators.supabase_auth.verify_token",
        lambda t: {"id": admin_user["supabase_uid"], "email": admin_user["email"]},
    )

    # Add image
    res_add = client.post(
        f"/api/v1/products/{prod_id}/images",
        json={"image_url": "https://img.com/sht1.jpg", "is_primary": True},
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert res_add.status_code == 201
    img_id = res_add.get_json()["data"]["id"]

    # Delete image
    res_del = client.delete(
        f"/api/v1/products/{prod_id}/images/{img_id}",
        headers={"Authorization": "Bearer mock-admin-token"},
    )
    assert res_del.status_code == 200
