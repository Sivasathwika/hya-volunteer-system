"""
Database connection and initialization.
This module sets up SQLAlchemy ORM and provides the database instance.

Why separate? Keep database setup decoupled from Flask app factory.
Allows models to import 'db' without circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create SQLAlchemy instance (without Flask app bound yet)
# App binding happens in app/__init__.py
db = SQLAlchemy()


class BaseModel(db.Model):
    """
    Abstract base model with common fields for all tables.
    
    Every table inherits from this, so we get consistent:
    - id (primary key)
    - created_at (when record was created)
    - updated_at (when record was last modified)
    
    This is a production pattern: Don't repeat these columns in every model.
    """
    
    __abstract__ = True  # This class is NOT mapped to a table
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<{self.__class__.__name__} id={self.id}>"
    
    def to_dict(self):
        """
        Convert model instance to dictionary.
        Useful for JSON serialization in APIs.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle datetime serialization
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result


def init_db(app):
    """
    Initialize database with Flask app.
    Called from app/__init__.py during app creation.
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    
    with app.app_context():
        # Import all models here to ensure they're registered with SQLAlchemy
        # before any database operations
        from app.models import (
            User, Volunteer, Skill, VolunteerSkill,
            Event, EventRegistration, Attendance,
            Donation, Certificate
        )
        
        # Create all tables if they don't exist
        db.create_all()
        print("✓ Database initialized. Tables created.")