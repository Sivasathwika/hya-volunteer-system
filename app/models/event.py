"""
Event models - Event management and registration workflow.

Design:
- Event: Event details (date, location, capacity)
- EventRegistration: Workflow table tracking registration state (pending → approved → attended)

Why separate registration from event?
- Workflow tracking: pending → approved → rejected → attended → no_show
- Capacity management: approved_count vs registered_count
- Audit trail: Who approved? When? Why rejected?
- Enables waitlists: registration_status captures position
"""

from app.database import BaseModel, db
from datetime import datetime


class Event(BaseModel):
    """
    Event model - Represents a volunteer event.
    
    Columns:
    - title, description: Event details
    - event_date, start_time, end_time: Scheduling
    - location: Where the event happens
    - capacity: Max volunteers needed
    - current_registration_count: How many registered (for display)
    - status: 'draft' | 'published' | 'ongoing' | 'completed' | 'cancelled'
    - created_by: Which admin created this event
    - created_at, updated_at: Audit fields
    """
    
    __tablename__ = 'events'
    
    # Status constants
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_ONGOING = 'ongoing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    VALID_STATUSES = [
        STATUS_DRAFT, STATUS_PUBLISHED, STATUS_ONGOING,
        STATUS_COMPLETED, STATUS_CANCELLED
    ]
    
    # Columns
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    current_registration_count = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(
        db.String(50),
        default=STATUS_DRAFT,
        nullable=False,
        index=True
    )
    
    # Foreign key to User (admin who created event)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        index=True
    )
    
    # Relationships
    registrations = db.relationship(
        'EventRegistration',
        backref='event',
        lazy='dynamic',
        cascade='all, delete-orphan',
        foreign_keys='EventRegistration.event_id'
    )
    
    attendances = db.relationship(
        'Attendance',
        backref='event',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    donations = db.relationship(
        'Donation',
        backref='event',
        lazy='dynamic',
        foreign_keys='Donation.event_id'
    )
    
    certificates = db.relationship(
        'Certificate',
        backref='event',
        lazy='dynamic',
        foreign_keys='Certificate.event_id'
    )
    
    def __repr__(self):
        return f"<Event {self.title} on {self.event_date}>"
    
    def publish(self):
        """Change status from draft to published."""
        if self.status == self.STATUS_DRAFT:
            self.status = self.STATUS_PUBLISHED
            db.session.commit()
    
    def cancel(self):
        """Cancel the event."""
        self.status = self.STATUS_CANCELLED
        db.session.commit()
    
    def has_capacity(self) -> bool:
        """Check if event still has available slots."""
        # Count approved registrations
        approved_count = EventRegistration.query.filter_by(
            event_id=self.id,
            registration_status=EventRegistration.STATUS_APPROVED
        ).count()
        return approved_count < self.capacity
    
    def get_available_slots(self) -> int:
        """Get number of available slots."""
        approved_count = EventRegistration.query.filter_by(
            event_id=self.id,
            registration_status=EventRegistration.STATUS_APPROVED
        ).count()
        return max(0, self.capacity - approved_count)
    
    def get_pending_registrations(self):
        """Get all pending registrations waiting for approval."""
        return self.registrations.filter_by(
            registration_status=EventRegistration.STATUS_PENDING
        ).all()
    
    def get_approved_volunteers(self):
        """Get all approved volunteers for this event."""
        regs = self.registrations.filter_by(
            registration_status=EventRegistration.STATUS_APPROVED
        ).all()
        return [reg.volunteer for reg in regs]
    
    def get_attended_volunteers(self):
        """Get all volunteers who attended."""
        attendances = self.attendances.all()
        return [att.volunteer for att in attendances]
    
    def get_attendance_count(self) -> int:
        """How many volunteers actually showed up?"""
        return self.attendances.count()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_date': str(self.event_date),
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'location': self.location,
            'capacity': self.capacity,
            'available_slots': self.get_available_slots(),
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class EventRegistration(BaseModel):
    """
    Event Registration workflow table.
    
    Tracks volunteer registration state throughout the workflow:
    - pending: Just registered, waiting for admin approval
    - approved: Admin approved, volunteer confirmed attending
    - rejected: Admin rejected (capacity, not suitable)
    - attended: Checked in and attended
    - no_show: Registered but didn't attend
    
    Columns:
    - volunteer_id, event_id: The registration
    - registration_status: Current state in workflow
    - registered_at: When volunteer registered
    - approved_by, approved_at: Admin approval details
    - notes: Rejection reason, comments
    - waitlist_position: If waiting list is full
    """
    
    __tablename__ = 'event_registrations'
    
    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_ATTENDED = 'attended'
    STATUS_NO_SHOW = 'no_show'
    VALID_STATUSES = [
        STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED,
        STATUS_ATTENDED, STATUS_NO_SHOW
    ]
    
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
    
    # Workflow
    registration_status = db.Column(
        db.String(50),
        default=STATUS_PENDING,
        nullable=False,
        index=True
    )
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)  # Rejection reason, feedback, etc.
    waitlist_position = db.Column(db.Integer)  # If on waitlist
    
    # Composite unique: Volunteer can register for event only once
    __table_args__ = (
        db.UniqueConstraint('volunteer_id', 'event_id', name='uq_volunteer_event_registration'),
    )
    
    def __repr__(self):
        return f"<EventRegistration {self.volunteer.email} → {self.event.title}>"
    
    def approve(self, admin_id: int, notes: str = None):
        """Admin approves this registration."""
        self.registration_status = self.STATUS_APPROVED
        self.approved_by = admin_id
        self.approved_at = datetime.utcnow()
        self.notes = notes
        db.session.commit()
    
    def reject(self, admin_id: int, reason: str):
        """Admin rejects this registration."""
        self.registration_status = self.STATUS_REJECTED
        self.approved_by = admin_id
        self.approved_at = datetime.utcnow()
        self.notes = reason
        db.session.commit()
    
    def mark_attended(self):
        """Mark as attended (usually set by attendance check-in)."""
        self.registration_status = self.STATUS_ATTENDED
        db.session.commit()
    
    def mark_no_show(self):
        """Mark as no-show (event finished, volunteer never checked in)."""
        self.registration_status = self.STATUS_NO_SHOW
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'volunteer_id': self.volunteer_id,
            'event_id': self.event_id,
            'status': self.registration_status,
            'registered_at': self.registered_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'waitlist_position': self.waitlist_position
        }