from datetime import datetime, timezone
from app.extensions import db
from app.models.base import TimestampMixin


class Coupon(db.Model, TimestampMixin):
    """Discount coupon model."""

    __tablename__ = "coupons"

    __table_args__ = (
        db.CheckConstraint(
            "discount_type IN ('percentage', 'fixed')",
            name="chk_coupon_discount_type_valid",
        ),
        db.CheckConstraint("discount_value > 0", name="chk_coupon_discount_value_positive"),
        db.CheckConstraint(
            "minimum_order_amount >= 0", name="chk_coupon_min_order_non_negative"
        ),
        db.CheckConstraint(
            "maximum_discount_amount IS NULL OR maximum_discount_amount > 0",
            name="chk_coupon_max_discount_positive",
        ),
        db.CheckConstraint(
            "usage_limit IS NULL OR usage_limit > 0",
            name="chk_coupon_usage_limit_positive",
        ),
        db.CheckConstraint("per_user_limit > 0", name="chk_coupon_per_user_limit_positive"),
        db.CheckConstraint("used_count >= 0", name="chk_coupon_used_count_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, index=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_order_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    maximum_discount_amount = db.Column(db.Numeric(10, 2), nullable=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    per_user_limit = db.Column(db.Integer, default=1, nullable=False)
    used_count = db.Column(db.Integer, default=0, nullable=False)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    usages = db.relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Coupon {self.code} ({self.discount_type}: {self.discount_value})>"


class CouponUsage(db.Model):
    """Audit log of coupon usage per user and order."""

    __tablename__ = "coupon_usages"

    __table_args__ = (
        db.CheckConstraint("discount_amount >= 0", name="chk_coupon_usage_discount_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    coupon_id = db.Column(
        db.Integer,
        db.ForeignKey("coupons.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id = db.Column(
        db.String(64),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False)
    used_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    coupon = db.relationship("Coupon", back_populates="usages")
    user = db.relationship("User", back_populates="coupon_usages")
    order = db.relationship("Order", back_populates="coupon_usages")

    def __repr__(self):
        return f"<CouponUsage Coupon:{self.coupon_id} User:{self.user_id} Order:{self.order_id}>"
