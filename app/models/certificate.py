"""
Certificate model - Track issued certificates.

Design:
- event_id is NULLABLE (can issue for general participation, milestones)
- pdf_url: Path to generated PDF certificate
- verification_code: Unique code for verification (can be shared publicly)

Use case:
- Volunteer attends 10 events → Generate certificate
- Volunteer donates significant amount → Generate appreciation certificate
- Event organizer awards special volunteer → Generate special certificate
"""

from app.database import BaseModel, db
from datetime import datetime
import uuid


class Certificate(BaseModel):
    """
    Certificate management - Track issued certificates.
    
    Columns:
    - volunteer_id: Recipient of certificate
    - event_id: Associated event (nullable - can be general cert)
    - certificate_type: 'attendance' | 'appreciation' | 'milestone'
    - issued_date: When certificate was issued
    - pdf_url: Path to PDF file
    - verification_code: Unique code for verification
    - hours_credited: Hours attributed to this certificate
    """
    
    __tablename__ = 'certificates'
    
    # Type constants
    TYPE_ATTENDANCE = 'attendance'
    TYPE_APPRECIATION = 'appreciation'
    TYPE_MILESTONE = 'milestone'
    VALID_TYPES = [TYPE_ATTENDANCE, TYPE_APPRECIATION, TYPE_MILESTONE]
    
    # Foreign keys
    volunteer_id = db.Column(
        db.Integer,
        db.ForeignKey('volunteers.id'),
        nullable=False,
        index=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.id'),
        index=True
    )
    
    # Certificate details
    certificate_type = db.Column(
        db.String(50),
        default=TYPE_ATTENDANCE,
        nullable=False
    )
    issued_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # PDF storage
    pdf_url = db.Column(db.String(255))  # Path or URL to PDF file
    
    # Verification
    verification_code = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Hours
    hours_credited = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        cert_type = self.certificate_type.upper()
        return f"<Certificate {cert_type} for {self.volunteer.email}>"
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate unique verification code."""
        return str(uuid.uuid4())[:8].upper()
    
    @classmethod
    def create_attendance_certificate(cls, volunteer, event, hours=0):
        """Create attendance certificate for volunteer at event."""
        cert = cls(
            volunteer_id=volunteer.id,
            event_id=event.id,
            certificate_type=cls.TYPE_ATTENDANCE,
            hours_credited=hours,
            verification_code=cls.generate_verification_code()
        )
        db.session.add(cert)
        db.session.commit()
        return cert
    
    @classmethod
    def create_appreciation_certificate(cls, volunteer, hours=0):
        """Create appreciation certificate (no event)."""
        cert = cls(
            volunteer_id=volunteer.id,
            certificate_type=cls.TYPE_APPRECIATION,
            hours_credited=hours,
            verification_code=cls.generate_verification_code()
        )
        db.session.add(cert)
        db.session.commit()
        return cert
    
    @classmethod
    def create_milestone_certificate(cls, volunteer, milestone_name, hours=0):
        """Create milestone certificate."""
        cert = cls(
            volunteer_id=volunteer.id,
            certificate_type=cls.TYPE_MILESTONE,
            hours_credited=hours,
            verification_code=cls.generate_verification_code()
        )
        db.session.add(cert)
        db.session.commit()
        return cert
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'volunteer_id': self.volunteer_id,
            'event_id': self.event_id,
            'type': self.certificate_type,
            'issued_date': self.issued_date.isoformat(),
            'verification_code': self.verification_code,
            'hours_credited': self.hours_credited,
            'pdf_url': self.pdf_url
        }