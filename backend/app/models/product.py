from app.extensions import db
from app.models.base import TimestampMixin


class Product(db.Model, TimestampMixin):
    """Product model for e-commerce items."""

    __tablename__ = "products"

    __table_args__ = (
        db.CheckConstraint("price >= 0", name="chk_product_price_non_negative"),
        db.CheckConstraint(
            "compare_at_price IS NULL OR compare_at_price >= 0",
            name="chk_product_compare_price_non_negative",
        ),
        db.CheckConstraint("stock_quantity >= 0", name="chk_product_stock_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, index=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    compare_at_price = db.Column(db.Numeric(10, 2), nullable=True)
    sku = db.Column(db.String(100), unique=True, index=True, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    weight = db.Column(db.Numeric(10, 3), default=0.500, nullable=False)  # Weight in KG
    tagline = db.Column(db.String(255), nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, index=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, index=True, nullable=False)
    is_trending = db.Column(db.Boolean, default=False, index=True, nullable=False)

    # Relationships
    category = db.relationship("Category", back_populates="products")
    images = db.relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    wishlist_items = db.relationship("WishlistItem", back_populates="product", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="product")
    reviews = db.relationship("Review", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name} (SKU: {self.sku})>"
