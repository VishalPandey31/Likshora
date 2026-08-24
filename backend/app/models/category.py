from app.extensions import db
from app.models.base import TimestampMixin


class Category(db.Model, TimestampMixin):
    """Category model representing product taxonomy."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, index=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    products = db.relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"
