from datetime import datetime, timezone
from app.extensions import db


class SearchHistory(db.Model):
    """Customer search activity log model."""

    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(64),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    search_query = db.Column("query", db.String(255), nullable=False)
    results_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )

    # Relationship
    user = db.relationship("User", back_populates="search_history")

    def __repr__(self):
        return f"<SearchHistory User:{self.user_id} Query:'{self.search_query}'>"
