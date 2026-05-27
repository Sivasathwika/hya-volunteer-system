"""
Attendance model - QR-based check-in/check-out tracking.

Features:
- Unique QR code per volunteer-event pair
- Check-in and check-out time tracking
- Automatic hours calculation
- Status tracking (incomplete, checked_in, checked_out)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Float, String, ForeignKey
from app.database import db, BaseModel


class Attendance(BaseModel):
    """
    Attendance tracking with QR codes.
    
    Flow:
    1. When registration approved → create Attendance with QR code
    2. Volunteer scans QR to check in
    3. Volunteer scans again to check out
    4. System calculates hours_served
    """
    
    __tablename__ = 'attendance'
    
    # Statuses
    STATUS_INCOMPLETE = 'incomplete'
    STATUS_CHECKED_IN = 'checked_in'
    STATUS_CHECKED_OUT = 'checked_out'
    
    VALID_STATUSES = [STATUS_INCOMPLETE, STATUS_CHECKED_IN, STATUS_CHECKED_OUT]
    
    # Columns
    volunteer_id = Column(Integer, ForeignKey('volunteers.id'), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    qr_code = Column(String(255), unique=True, nullable=False, index=True)
    
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    hours_served = Column(Float, default=0.0)
    
    status = Column(String(50), default=STATUS_INCOMPLETE, nullable=False)
    
    # Relationships
    volunteer = db.relationship('Volunteer', backref='attendances')
    event = db.relationship('Event', backref='attendances')
    
    def __repr__(self):
        return f'<Attendance {self.volunteer.email} @ {self.event.title}>'
    
    @staticmethod
    def generate_qr_code():
        """Generate unique QR code using UUID."""
        return str(uuid.uuid4())
    
    def check_in(self):
        """Record check-in time and update status."""
        self.check_in_time = datetime.utcnow()
        self.status = self.STATUS_CHECKED_IN
        db.session.commit()
    
    def check_out(self):
        """
        Record check-out time and calculate hours served.
        
        Raises ValueError if check-in never happened.
        """
        if not self.check_in_time:
            raise ValueError('Cannot check out without check-in')
        
        self.check_out_time = datetime.utcnow()
        self.status = self.STATUS_CHECKED_OUT
        
        # Calculate hours served (rounded to 2 decimal places)
        duration = self.check_out_time - self.check_in_time
        self.hours_served = round(duration.total_seconds() / 3600, 2)
        
        # Update volunteer's total hours
        self.volunteer.total_hours_served = (self.volunteer.total_hours_served or 0) + self.hours_served
        
        db.session.commit()
    
    def mark_incomplete(self):
        """Mark as incomplete (no-show - checked in but never checked out)."""
        self.status = self.STATUS_INCOMPLETE
        self.hours_served = 0.0
        db.session.commit()