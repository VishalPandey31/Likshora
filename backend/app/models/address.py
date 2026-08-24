from app.extensions import db
from app.models.base import TimestampMixin


class Address(db.Model, TimestampMixin):
    """Customer shipping and billing address model."""

    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(64),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=True)
    recipient = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    flat = db.Column(db.String(255), nullable=True)
    street = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), default="India", nullable=True)
    is_default = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="addresses")
    orders = db.relationship("Order", back_populates="address")

    @property
    def full_name(self) -> str:
        return self.recipient or self.name or ""

    @full_name.setter
    def full_name(self, value: str):
        self.recipient = value
        self.name = value

    @property
    def address_line1(self) -> str:
        return f"{self.flat or ''} {self.street or ''}".strip()

    @address_line1.setter
    def address_line1(self, value: str):
        self.flat = value

    @property
    def address_line2(self) -> str | None:
        return self.street

    @address_line2.setter
    def address_line2(self, value: str | None):
        self.street = value

    @property
    def postal_code(self) -> str:
        return self.pincode or ""

    @postal_code.setter
    def postal_code(self, value: str):
        self.pincode = value

    def __repr__(self):
        return f"<Address {self.full_name}, {self.city} (Default: {self.is_default})>"
