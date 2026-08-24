import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.base import TimestampMixin


class User(db.Model, TimestampMixin):
    """User profile model representing customers and administrators."""

    __tablename__ = "users"

    id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    supabase_uid = db.Column(db.String(64), unique=True, index=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), default="customer", nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default="Active", nullable=False)

    # Relationships
    addresses = db.relationship("Address", back_populates="user", cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    wishlist_items = db.relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user")
    coupon_usages = db.relationship("CouponUsage", back_populates="user")
    login_logs = db.relationship("CustomerLoginLog", back_populates="user", cascade="all, delete-orphan")
    search_history = db.relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "supabase_uid" in kwargs and kwargs["supabase_uid"] and "id" not in kwargs:
            kwargs["id"] = kwargs["supabase_uid"]
        if "phone" not in kwargs or kwargs["phone"] is None:
            kwargs["phone"] = ""
        super().__init__(**kwargs)

    @property
    def is_active(self) -> bool:
        return self.status == "Active"

    @is_active.setter
    def is_active(self, value: bool):
        self.status = "Active" if value else "Blocked"

    @property
    def email_verified(self) -> bool:
        return self.is_verified

    @email_verified.setter
    def email_verified(self, value: bool):
        self.is_verified = bool(value)

    def __repr__(self):
        return f"<User {self.email} ({self.status})>"


class CustomerLoginLog(db.Model):
    """Audit log for user login attempts."""

    __tablename__ = "customer_login_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(64),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=True,
    )
    user_name = db.Column(db.String(100), nullable=True)
    user_email = db.Column(db.String(255), nullable=True)
    day_of_week = db.Column(db.String(20), nullable=True)

    # Relationship
    user = db.relationship("User", back_populates="login_logs")

    @property
    def login_at(self):
        return self.timestamp

    @property
    def success(self):
        return True

    def __repr__(self):
        return f"<CustomerLoginLog User:{self.user_id} Email:{self.user_email}>"
