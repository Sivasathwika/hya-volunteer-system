"""
Base model with common fields.
All models inherit from this to avoid code duplication.
"""

from app.database import BaseModel, db
from datetime import datetime


class TimestampMixin:
    """
    Mixin providing created_at and updated_at fields.
    SQLAlchemy models that need audit trails inherit this.
    """
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )