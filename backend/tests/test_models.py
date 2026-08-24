import pytest
from sqlalchemy import inspect
from app.models import (
    User,
    CustomerLoginLog,
    Category,
    Product,
    ProductImage,
    CartItem,
    WishlistItem,
    Address,
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    Payment,
    Shipment,
)


def test_table_names_exist(app):
    """Test that all 14 model table names are properly mapped."""
    models = [
        User,
        CustomerLoginLog,
        Category,
        Product,
        ProductImage,
        CartItem,
        WishlistItem,
        Address,
        Coupon,
        CouponUsage,
        Order,
        OrderItem,
        Payment,
        Shipment,
    ]
    expected_tables = {
        "users",
        "customer_login_logs",
        "categories",
        "products",
        "product_images",
        "cart_items",
        "wishlist_items",
        "addresses",
        "coupons",
        "coupon_usages",
        "orders",
        "order_items",
        "payments",
        "shipments",
    }
    actual_tables = {model.__tablename__ for model in models}
    assert actual_tables == expected_tables


def test_user_model_instantiation(app):
    """Test User model fields and default values."""
    user = User(
        name="Test Customer",
        email="customer@example.com",
        phone="+919876543210",
        role="customer",
        is_active=True,
        email_verified=False,
    )
    assert user.name == "Test Customer"
    assert user.email == "customer@example.com"
    assert user.role == "customer"
    assert user.is_active is True
    assert user.email_verified is False


def test_product_model_instantiation(app):
    """Test Product model fields and relationships."""
    category = Category(name="Apparel", slug="apparel")
    product = Product(
        name="Classic Cotton T-Shirt",
        slug="classic-cotton-tshirt",
        sku="TSH-COT-001",
        price=799.00,
        stock_quantity=50,
        category=category,
    )
    assert product.name == "Classic Cotton T-Shirt"
    assert product.sku == "TSH-COT-001"
    assert float(product.price) == 799.00
    assert product.stock_quantity == 50
    assert product.category.name == "Apparel"


def test_cart_and_wishlist_unique_constraints(app):
    """Test cart and wishlist item unique composite constraint definitions."""
    cart_table = CartItem.__table__
    cart_uniques = [c.name for c in cart_table.constraints if hasattr(c, "name")]
    assert "uq_cart_user_product" in cart_uniques

    wishlist_table = WishlistItem.__table__
    wishlist_uniques = [c.name for c in wishlist_table.constraints if hasattr(c, "name")]
    assert "uq_wishlist_user_product" in wishlist_uniques


def test_order_model_relationships(app):
    """Test Order model field definitions and relationship attributes."""
    order = Order(
        order_number="ORD-2026-0001",
        subtotal=1500.00,
        discount_amount=200.00,
        shipping_amount=50.00,
        total_amount=1350.00,
        payment_method="online",
        payment_status="paid",
        order_status="confirmed",
    )
    assert order.order_number == "ORD-2026-0001"
    assert float(order.total_amount) == 1350.00
    assert order.payment_method == "online"
    assert order.payment_status == "paid"
    assert order.order_status == "confirmed"
    assert hasattr(order, "order_items")
    assert hasattr(order, "payments")
    assert hasattr(order, "shipments")
    assert hasattr(order, "coupon_usages")
