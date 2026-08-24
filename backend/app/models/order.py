from datetime import datetime, timezone
from app.extensions import db
from app.models.base import TimestampMixin


class Order(db.Model, TimestampMixin):
    """Order header model."""

    __tablename__ = "orders"

    __table_args__ = (
        db.CheckConstraint("subtotal >= 0", name="chk_order_subtotal_non_negative"),
        db.CheckConstraint("discount_amount >= 0", name="chk_order_discount_non_negative"),
        db.CheckConstraint("shipping_fee >= 0", name="chk_order_shipping_non_negative"),
        db.CheckConstraint("grand_total >= 0", name="chk_order_total_non_negative"),
        db.CheckConstraint(
            "status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned')",
            name="chk_order_status_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(64),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    address_id = db.Column(
        db.Integer,
        db.ForeignKey("addresses.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    order_number = db.Column(db.String(50), unique=True, index=True, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=True)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=True)
    shipping_fee = db.Column(db.Numeric(10, 2), default=0.00, nullable=True)
    grand_total = db.Column(db.Numeric(10, 2), nullable=True)
    payment_method = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(30), default="pending", index=True, nullable=True)
    contact_name = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    shipping_address_snapshot = db.Column(db.Text, nullable=True)

    # Properties for backward compatibility with existing API queries
    @property
    def total_amount(self):
        return self.grand_total

    @total_amount.setter
    def total_amount(self, value):
        self.grand_total = value

    def _get_snapshot_dict(self):
        if not self.shipping_address_snapshot:
            return {}
        try:
            import json
            return json.loads(self.shipping_address_snapshot)
        except Exception:
            return {}

    def _update_snapshot_dict(self, key, val):
        import json
        d = self._get_snapshot_dict()
        d[key] = val
        self.shipping_address_snapshot = json.dumps(d)

    @property
    def order_status(self):
        return self.status

    @order_status.setter
    def order_status(self, value):
        self.status = value

    @property
    def payment_status(self):
        if hasattr(self, "_payment_status_val") and self._payment_status_val is not None:
            return self._payment_status_val
        if self.payments and len(self.payments) > 0:
            return self.payments[0].status
        return "pending" if self.status != "cancelled" else "failed"

    @payment_status.setter
    def payment_status(self, value):
        self._payment_status_val = value

    @property
    def shipping_amount(self):
        return self.shipping_fee or 0.0

    @shipping_amount.setter
    def shipping_amount(self, value):
        self.shipping_fee = value

    @property
    def shipping_full_name(self):
        return self.contact_name

    @shipping_full_name.setter
    def shipping_full_name(self, value):
        self.contact_name = value

    @property
    def shipping_phone(self):
        return self.contact_phone

    @shipping_phone.setter
    def shipping_phone(self, value):
        self.contact_phone = value

    @property
    def shipping_address_line1(self):
        return self._get_snapshot_dict().get("address_line1", "")

    @shipping_address_line1.setter
    def shipping_address_line1(self, value):
        self._update_snapshot_dict("address_line1", value)

    @property
    def shipping_city(self):
        return self._get_snapshot_dict().get("city", "")

    @shipping_city.setter
    def shipping_city(self, value):
        self._update_snapshot_dict("city", value)

    @property
    def shipping_state(self):
        return self._get_snapshot_dict().get("state", "")

    @shipping_state.setter
    def shipping_state(self, value):
        self._update_snapshot_dict("state", value)

    @property
    def shipping_postal_code(self):
        return self._get_snapshot_dict().get("postal_code", "")

    @shipping_postal_code.setter
    def shipping_postal_code(self, value):
        self._update_snapshot_dict("postal_code", value)

    @property
    def shipping_country(self):
        return self._get_snapshot_dict().get("country", "")

    @shipping_country.setter
    def shipping_country(self, value):
        self._update_snapshot_dict("country", value)

    # Override created_at index for frequent timeline querying
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=True,
    )

    # Relationships
    user = db.relationship("User", back_populates="orders")
    address = db.relationship("Address", back_populates="orders")
    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    shipments = db.relationship("Shipment", back_populates="order", cascade="all, delete-orphan")
    coupon_usages = db.relationship("CouponUsage", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number} ({self.status})>"


class OrderItem(db.Model):
    """Order line item snapshot model."""

    __tablename__ = "order_items"

    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="chk_order_item_quantity_positive"),
        db.CheckConstraint("unit_price >= 0", name="chk_order_item_unit_price_non_negative"),
        db.CheckConstraint("subtotal >= 0", name="chk_order_item_subtotal_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    product_name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    order = db.relationship("Order", back_populates="order_items")
    product = db.relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem Order:{self.order_id} Product:{self.sku} Qty:{self.quantity}>"
