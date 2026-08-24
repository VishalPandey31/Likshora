from datetime import datetime, timezone
from app.extensions import db
from app.models.base import TimestampMixin


class Payment(db.Model, TimestampMixin):
    """Payment transaction model supporting online and COD payments."""

    __tablename__ = "payments"

    __table_args__ = (
        db.CheckConstraint("amount >= 0", name="chk_payment_amount_non_negative"),
        db.CheckConstraint(
            "status IN ('created', 'pending', 'authorized', 'captured', 'failed', 'refunded')",
            name="chk_payment_status_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    payment_method = db.Column(db.String(30), nullable=False)  # 'cod', 'online', 'card', 'upi', etc.
    provider = db.Column(db.String(50), default="razorpay", nullable=False)
    provider_payment_id = db.Column(db.String(100), unique=True, index=True, nullable=True)
    provider_order_id = db.Column(db.String(100), index=True, nullable=True)
    razorpay_signature = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default="INR", nullable=False)
    status = db.Column(db.String(30), default="created", nullable=False)
    failure_reason = db.Column(db.Text, nullable=True)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationship
    order = db.relationship("Order", back_populates="payments")

    def __repr__(self):
        return f"<Payment Order:{self.order_id} ProviderID:{self.provider_payment_id} Status:{self.status}>"


class PaymentWebhookEvent(db.Model, TimestampMixin):
    """Audit log and idempotency tracking table for Razorpay Webhook events."""

    __tablename__ = "payment_webhook_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), default="processed", nullable=False)
    processed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<PaymentWebhookEvent {self.event_id} ({self.event_type})>"
