"""
Attendance model - Real-world volunteer tracking.

Design:
- Separate from EventRegistration ("I want to come" vs "I actually came")
- Tracks check-in and check-out times
- Calculates hours served
- Stores QR code for verification

Why QR codes?
- Touch-free check-in (no sign sheet to pass around)
- Hard to forge (unique code per volunteer + event)
- Audit trail: When did they check in?
- Scalable: Works for 10 people or 10,000
"""

from app.database import BaseModel, db
from datetime import datetime
import uuid


class Attendance(BaseModel):
    """
    Attendance tracking - Who came, when, for how long?
    
    Columns:
    - volunteer_id, event_id: Which volunteer at which event
    - check_in_time: When they arrived
    - check_out_time: When they left (nullable - may not have checked out)
    - qr_code: Unique identifier for verification
    - status: 'checked_in' | 'checked_out' | 'incomplete'
    - hours_served: Calculated from check_in/out times
    """
    
    __tablename__ = 'attendance'
    
    # Status constants
    STATUS_CHECKED_IN = 'checked_in'
    STATUS_CHECKED_OUT = 'checked_out'
    STATUS_INCOMPLETE = 'incomplete'
    VALID_STATUSES = [STATUS_CHECKED_IN, STATUS_CHECKED_OUT, STATUS_INCOMPLETE]
    
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
        nullable=False,
        index=True
    )
    
    # Tracking
    check_in_time = db.Column(db.DateTime, nullable=False)
    check_out_time = db.Column(db.DateTime)  # Nullable - may not have checked out
    qr_code = db.Column(db.String(255), unique=True, nullable=False, index=True)
    status = db.Column(
        db.String(50),
        default=STATUS_CHECKED_IN,
        nullable=False
    )
    hours_served = db.Column(db.Float)  # Calculated when they check out
    
    # Composite unique: Volunteer can attend event only once
    __table_args__ = (
        db.UniqueConstraint('volunteer_id', 'event_id', name='uq_volunteer_event_attendance'),
    )
    
    def __repr__(self):
        return f"<Attendance {self.volunteer.email} @ {self.event.title}>"
    
    @staticmethod
    def generate_qr_code() -> str:
        """Generate unique QR code identifier."""
        return str(uuid.uuid4())
    
    def check_out(self):
        """Volunteer checks out. Calculate hours served."""
        self.check_out_time = datetime.utcnow()
        self.status = self.STATUS_CHECKED_OUT
        
        # Calculate hours served
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            self.hours_served = delta.total_seconds() / 3600  # Convert to hours
        
        db.session.commit()
    
    def mark_incomplete(self):
        """Mark as incomplete (volunteer checked in but never checked out)."""
        self.status = self.STATUS_INCOMPLETE
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'volunteer_id': self.volunteer_id,
            'event_id': self.event_id,
            'check_in_time': self.check_in_time.isoformat(),
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'status': self.status,
            'hours_served': self.hours_served,
            'qr_code': self.qr_code
        }