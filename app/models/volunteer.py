"""
Volunteer model - Inherits from User with additional volunteer-specific fields.

Single-table inheritance pattern:
- User table has role='volunteer' for volunteers
- Volunteer class extends User with volunteer-specific columns
- When role='volunteer', SQLAlchemy loads as Volunteer instance

Why this pattern?
- Volunteer-specific fields only in volunteers table (no null columns for admins)
- Relationship queries work on both (can query "all users")
- Can still filter by role when needed
"""

from app.database import BaseModel, db
from app.models.user import User


class Volunteer(User):
    """
    Volunteer extends User with volunteer-specific information.
    
    Additional Columns:
    - city: Volunteer's city
    - state: Volunteer's state/region
    - bio: Short bio/introduction
    - profile_complete: Has volunteer filled in all required fields?
    
    Relationships:
    - skills: Many-to-many with Skill through VolunteerSkill
    - registrations: Events this volunteer registered for
    - attendances: Events this volunteer actually attended
    - donations: Donations made by this volunteer
    - certificates: Certificates issued to this volunteer
    """
    
    __tablename__ = 'volunteers'
    
    # Foreign key to parent User table
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    
    # Volunteer-specific columns
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    bio = db.Column(db.Text)
    profile_complete = db.Column(db.Boolean, default=False, nullable=False)
    total_hours_served = db.Column(db.Float, default=0.0, nullable=False)
    
    # Relationships
    # Many-to-many with Skills through VolunteerSkill junction table
    skills = db.relationship(
        'VolunteerSkill',
        backref='volunteer',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # One-to-many with EventRegistration
    registrations = db.relationship(
        'EventRegistration',
        backref='volunteer',
        lazy='dynamic',
        foreign_keys='EventRegistration.volunteer_id',
        cascade='all, delete-orphan'
    )
    
    # One-to-many with Attendance
    attendances = db.relationship(
        'Attendance',
        backref='volunteer',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # One-to-many with Donation
    donations = db.relationship(
        'Donation',
        backref='donor',
        lazy='dynamic',
        foreign_keys='Donation.volunteer_id',
        cascade='all, delete-orphan'
    )
    
    # One-to-many with Certificate
    certificates = db.relationship(
        'Certificate',
        backref='volunteer',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Polymorphic identity: When role='volunteer', load as Volunteer
    __mapper_args__ = {
        'polymorphic_identity': User.ROLE_VOLUNTEER
    }
    
    def __repr__(self):
        return f"<Volunteer {self.email} - {self.full_name()}>"
    
    def get_skills(self):
        """Get list of all skills this volunteer has."""
        return [vs.skill for vs in self.skills.all()]
    
    def add_skill(self, skill, proficiency_level='beginner', years_exp=0):
        """
        Add a skill to this volunteer's profile.
        
        Args:
            skill: Skill instance
            proficiency_level: 'beginner', 'intermediate', or 'expert'
            years_exp: Years of experience with this skill
        """
        from app.models.skill import VolunteerSkill
        
        # Check if already has this skill
        existing = VolunteerSkill.query.filter_by(
            volunteer_id=self.id,
            skill_id=skill.id
        ).first()
        
        if existing:
            existing.proficiency_level = proficiency_level
            existing.years_of_experience = years_exp
        else:
            vs = VolunteerSkill(
                volunteer_id=self.id,
                skill_id=skill.id,
                proficiency_level=proficiency_level,
                years_of_experience=years_exp
            )
            db.session.add(vs)
        
        db.session.commit()
    
    def remove_skill(self, skill):
        """Remove a skill from this volunteer's profile."""
        from app.models.skill import VolunteerSkill
        
        VolunteerSkill.query.filter_by(
            volunteer_id=self.id,
            skill_id=skill.id
        ).delete()
        db.session.commit()
    
    def get_registered_events(self):
        """Get list of events this volunteer registered for."""
        return [reg.event for reg in self.registrations.all()]
    
    def get_attended_events(self):
        """Get list of events this volunteer actually attended."""
        attended_ids = set()
        for attendance in self.attendances.all():
            attended_ids.add(attendance.event_id)
        
        from app.models.event import Event
        return Event.query.filter(Event.id.in_(attended_ids)).all()
    
    def get_total_hours(self):
        """Calculate total volunteer hours from all attendances."""
        total = 0
        for attendance in self.attendances.all():
            if attendance.hours_served:
                total += attendance.hours_served
        return total
    
    def has_participated_in_event(self, event):
        """Check if volunteer has attended an event."""
        from app.models.attendance import Attendance
        return Attendance.query.filter_by(
            volunteer_id=self.id,
            event_id=event.id
        ).first() is not None
    
    def mark_profile_complete(self):
        """Mark volunteer profile as complete (all required fields filled)."""
        self.profile_complete = True
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary, include skills and hours."""
        data = super().to_dict()
        data['skills'] = [skill.skill.name for skill in self.skills.all()]
        data['total_hours_served'] = self.total_hours_served
        data['profile_complete'] = self.profile_complete
        return data