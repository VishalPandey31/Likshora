from datetime import datetime, timezone
from app.extensions import db


class ProductImage(db.Model):
    """Product image gallery item model."""

    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    image_url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    product = db.relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductImage Product:{self.product_id} Primary:{self.is_primary}>"
