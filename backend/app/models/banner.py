from datetime import datetime, timezone
from app.extensions import db
from app.models.base import TimestampMixin


class Banner(db.Model, TimestampMixin):
    """Banner model for hero slides, promotional banners, and marketing text."""

    __tablename__ = "banners"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    subtitle = db.Column(db.String(500), nullable=True)
    tagline = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(500), nullable=False)
    cta_text = db.Column(db.String(100), nullable=True)
    cta_link = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True, nullable=False)

    def __repr__(self):
        return f"<Banner id={self.id} title='{self.title}'>"
