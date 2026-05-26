"""
Models package - All database models.

Import all models here so they're registered with SQLAlchemy.
This ensures all relationships are set up correctly.

Usage:
    from app.models import User, Volunteer, Event, Skill, etc.
"""

from app.models.user import User
from app.models.volunteer import Volunteer
from app.models.skill import Skill, VolunteerSkill
from app.models.event import Event, EventRegistration
from app.models.attendance import Attendance
from app.models.donation import Donation
from app.models.certificate import Certificate

__all__ = [
    'User',
    'Volunteer',
    'Skill',
    'VolunteerSkill',
    'Event',
    'EventRegistration',
    'Attendance',
    'Donation',
    'Certificate'
]