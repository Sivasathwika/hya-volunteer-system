"""
User model - Single table with role-based inheritance.

Design Decision: Why single table instead of separate admin/volunteer tables?
- DRY: No duplicate columns (email, password, name, etc.)
- Easy authentication: One login endpoint works for both roles
- Flexible: Users can switch roles without data migration
- Real-world pattern: This is how production systems do it

Authentication vs Authorization:
- Authentication: "Are you who you say you are?" (login)
- Authorization: "Are you allowed to do this?" (role check)
"""

from app.database import BaseModel, db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re


class User(BaseModel):
    """
    Base user model for both admins and volunteers.
    
    Columns:
    - id: Primary key (auto-increment)
    - email: Unique identifier for login
    - password_hash: Hashed password (NEVER store plain text)
    - first_name, last_name: Full name
    - phone: Contact number
    - role: 'admin' or 'volunteer' (determines permissions)
    - is_active: Soft delete flag (disabled accounts)
    - created_at, updated_at: Audit fields
    """
    
    __tablename__ = 'users'
    
    # Enum-like values (not using Python Enum to keep it simple)
    ROLE_ADMIN = 'admin'
    ROLE_VOLUNTEER = 'volunteer'
    VALID_ROLES = [ROLE_ADMIN, ROLE_VOLUNTEER]
    
    # Columns
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(
        db.String(20),
        default=ROLE_VOLUNTEER,
        nullable=False,
        index=True
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    # Events created by this user (admin creates events)
    created_events = db.relationship(
        'Event',
        backref='creator',
        foreign_keys='Event.created_by',
        lazy='dynamic'
    )
    
    # Registrations approved by this user (admin approves registrations)
    approved_registrations = db.relationship(
        'EventRegistration',
        backref='approver',
        foreign_keys='EventRegistration.approved_by',
        lazy='dynamic'
    )
    
    # Donations verified by this user
    verified_donations = db.relationship(
        'Donation',
        backref='verifier',
        foreign_keys='Donation.verified_by',
        lazy='dynamic'
    )
    
    # Polymorphic identity for single-table inheritance
    # If role is 'volunteer', SQLAlchemy loads as Volunteer instance
    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': ROLE_ADMIN
    }
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
    
    def set_password(self, password: str) -> None:
        """
        Hash and store password.
        
        NEVER store passwords in plain text. Ever.
        Werkzeug uses bcrypt under the hood (strong hashing).
        
        Args:
            password: Plain text password from user
        """
        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """
        Verify plain text password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def _validate_password_strength(password: str) -> bool:
        """
        Enforce password security requirements.
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one number
        - At least one special character
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements
        """
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False
        return True
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == self.ROLE_ADMIN
    
    def is_volunteer(self) -> bool:
        """Check if user is a volunteer."""
        return self.role == self.ROLE_VOLUNTEER
    
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        This is a basic check. Use email-validator library in forms
        for more robust validation.
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @classmethod
    def get_by_email(cls, email: str):
        """Query user by email (case-insensitive)."""
        return cls.query.filter_by(email=email.lower()).first()
    
    def deactivate(self):
        """Soft delete: Mark user as inactive."""
        self.is_active = False
        db.session.commit()
    
    def activate(self):
        """Re-activate a deactivated user."""
        self.is_active = True
        db.session.commit()