from datetime import datetime, timezone
from app.extensions import db


class Review(db.Model):
    """Product review and rating model submitted by customers."""

    __tablename__ = "reviews"

    __table_args__ = (
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="chk_review_rating_range"),
        db.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="chk_review_status_valid"),
        db.UniqueConstraint("user_id", "product_id", name="uq_user_product_review"),
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
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending", index=True, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="reviews")
    product = db.relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<Review User:{self.user_id} Product:{self.product_id} Rating:{self.rating} Status:{self.status}>"
