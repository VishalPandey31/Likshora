from app.extensions import db
from app.models.base import TimestampMixin


class CartItem(db.Model, TimestampMixin):
    """Cart item model linking users with added products."""

    __tablename__ = "cart_items"

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
        db.CheckConstraint("quantity > 0", name="chk_cart_item_quantity_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(64),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="cart_items")
    product = db.relationship("Product", back_populates="cart_items")

    def __repr__(self):
        return f"<CartItem User:{self.user_id} Product:{self.product_id} Qty:{self.quantity}>"
