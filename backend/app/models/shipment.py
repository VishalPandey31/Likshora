from app.extensions import db
from app.models.base import TimestampMixin


class Shipment(db.Model, TimestampMixin):
    """Order fulfillment and shipment tracking model."""

    __tablename__ = "shipments"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'created', 'assigned', 'pickup_scheduled', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'cancelled', 'returned', 'failed')",
            name="chk_shipment_status_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    provider = db.Column(db.String(50), default="shiprocket", nullable=False)
    shipment_id = db.Column(db.String(100), unique=True, nullable=True)
    shiprocket_order_id = db.Column(db.String(100), nullable=True)
    awb_code = db.Column(db.String(100), unique=True, index=True, nullable=True)
    courier_name = db.Column(db.String(100), nullable=True)
    courier_id = db.Column(db.Integer, nullable=True)
    tracking_url = db.Column(db.String(500), nullable=True)
    pickup_token_number = db.Column(db.String(100), nullable=True)
    label_url = db.Column(db.String(500), nullable=True)
    manifest_url = db.Column(db.String(500), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="pending", nullable=False)
    pickup_scheduled_at = db.Column(db.DateTime(timezone=True), nullable=True)
    shipped_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    order = db.relationship("Order", back_populates="shipments")
    tracking_events = db.relationship("ShipmentTrackingEvent", back_populates="shipment", cascade="all, delete-orphan", order_by="ShipmentTrackingEvent.event_timestamp.asc()")

    def __repr__(self):
        return f"<Shipment Order:{self.order_id} AWB:{self.awb_code} Status:{self.status}>"


class ShipmentWebhookEvent(db.Model, TimestampMixin):
    """Shiprocket Webhook idempotency and audit log model."""

    __tablename__ = "shipment_webhook_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(100), unique=True, index=True, nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), default="processed", nullable=False)

    def __repr__(self):
        return f"<ShipmentWebhookEvent EventID:{self.event_id} Type:{self.event_type}>"


class ShipmentTrackingEvent(db.Model, TimestampMixin):
    """Shipment tracking historical events model."""

    __tablename__ = "shipment_tracking_events"

    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(
        db.Integer,
        db.ForeignKey("shipments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status = db.Column(db.String(50), nullable=False)
    external_status = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    event_timestamp = db.Column(db.DateTime(timezone=True), index=True, nullable=False)

    # Relationship
    shipment = db.relationship("Shipment", back_populates="tracking_events")

    def __repr__(self):
        return f"<ShipmentTrackingEvent Shipment:{self.shipment_id} Status:{self.status} Time:{self.event_timestamp}>"
