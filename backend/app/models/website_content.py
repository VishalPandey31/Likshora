from datetime import datetime, timezone
from app.extensions import db
from app.models.base import TimestampMixin


class RotatingModel(db.Model, TimestampMixin):
    """Rotating model carousel item model."""

    __tablename__ = "rotating_models"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    tagline = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True, nullable=False)

    def __repr__(self):
        return f"<RotatingModel {self.name}>"


class SiteContent(db.Model):
    """Key-value site settings and dynamic marketing content model."""

    __tablename__ = "site_contents"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, index=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<SiteContent {self.key}>"
