from datetime import datetime, timezone
from app.extensions import db


class WishlistItem(db.Model):
    """Wishlist item model linking users with saved products."""

    __tablename__ = "wishlist_items"

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
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
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="wishlist_items")
    product = db.relationship("Product", back_populates="wishlist_items")

    def __repr__(self):
        return f"<WishlistItem User:{self.user_id} Product:{self.product_id}>"
