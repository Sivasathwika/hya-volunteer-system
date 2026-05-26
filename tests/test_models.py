"""
Unit tests for models.

Tests cover:
- Model creation
- Relationships
- Business logic methods
- Data validation
"""

import pytest
from datetime import date, time
from app import db
from app.models import (
    User, Volunteer, Skill, VolunteerSkill,
    Event, EventRegistration, Attendance, Donation, Certificate
)


class TestUserModel:
    """Test User model."""
    
    def test_user_creation(self, app):
        """Test creating a user."""
        with app.app_context():
            user = User(
                email='test@hya.org',
                first_name='Test',
                last_name='User',
                role='admin'
            )
            user.set_password('Test@123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == 'test@hya.org'
            assert user.is_admin()
    
    def test_password_hashing(self, app):
        """Test password is hashed, not stored plain."""
        with app.app_context():
            user = User(
                email='test@hya.org',
                first_name='Test',
                last_name='User'
            )
            user.set_password('MyPassword@123')
            
            # Password should be hashed
            assert user.password_hash != 'MyPassword@123'
            # Should be able to verify correct password
            assert user.check_password('MyPassword@123')
            # Should reject wrong password
            assert not user.check_password('WrongPassword')
    
    def test_password_strength_validation(self, app):
        """Test weak passwords are rejected."""
        with app.app_context():
            user = User(email='test@hya.org', first_name='Test', last_name='User')
            
            # Weak passwords should raise error
            with pytest.raises(ValueError):
                user.set_password('weak')  # Too short
            
            with pytest.raises(ValueError):
                user.set_password('noupppercase123')  # No uppercase
            
            with pytest.raises(ValueError):
                user.set_password('NoNumbers!@#')  # No numbers
    
    def test_duplicate_email_rejected(self, app, admin_user):
        """Test duplicate emails are rejected (unique constraint)."""
        with app.app_context():
            user2 = User(
                email=admin_user.email,  # Same email
                first_name='Another',
                last_name='User'
            )
            user2.set_password('Test@123')
            db.session.add(user2)
            
            with pytest.raises(Exception):  # Integrity error
                db.session.commit()


class TestVolunteerModel:
    """Test Volunteer model."""
    
    def test_volunteer_creation(self, app):
        """Test creating a volunteer."""
        with app.app_context():
            volunteer = Volunteer(
                email='vol@hya.org',
                first_name='John',
                last_name='Doe',
                city='Hyderabad',
                state='Telangana'
            )
            volunteer.set_password('Vol@123')
            db.session.add(volunteer)
            db.session.commit()
            
            assert volunteer.id is not None
            assert volunteer.role == 'volunteer'
            assert volunteer.city == 'Hyderabad'
    
    def test_add_skill_to_volunteer(self, app, volunteer_user, skill):
        """Test adding skills to volunteer."""
        with app.app_context():
            volunteer_user.add_skill(skill, 'intermediate', 2)
            
            skills = volunteer_user.get_skills()
            assert len(skills) == 1
            assert skills[0].name == 'Python'
    
    def test_duplicate_skill_update(self, app, volunteer_user, skill):
        """Test adding same skill updates proficiency."""
        with app.app_context():
            volunteer_user.add_skill(skill, 'beginner', 1)
            volunteer_user.add_skill(skill, 'expert', 5)  # Should update
            
            skills_count = VolunteerSkill.query.filter_by(
                volunteer_id=volunteer_user.id,
                skill_id=skill.id
            ).count()
            
            assert skills_count == 1  # Still just one skill
            vs = VolunteerSkill.query.filter_by(
                volunteer_id=volunteer_user.id,
                skill_id=skill.id
            ).first()
            assert vs.proficiency_level == 'expert'


class TestEventModel:
    """Test Event model."""
    
    def test_event_creation(self, event):
        """Test creating an event."""
        assert event.id is not None
        assert event.title == 'Park Cleanup'
        assert event.status == 'published'
    
    def test_event_capacity_check(self, app, event):
        """Test event capacity checking."""
        with app.app_context():
            assert event.has_capacity()
            assert event.get_available_slots() == 50
    
    def test_publish_event(self, app):
        """Test publishing a draft event."""
        with app.app_context():
            from app.models import User
            admin = User.query.filter_by(role='admin').first()
            
            event = Event(
                title='Test Event',
                event_date=date(2024, 12, 25),
                start_time=time(9, 0),
                end_time=time(12, 0),
                location='Test Location',
                capacity=10,
                created_by=admin.id,
                status='draft'
            )
            db.session.add(event)
            db.session.commit()
            
            assert event.status == 'draft'
            event.publish()
            assert event.status == 'published'


class TestEventRegistrationWorkflow:
    """Test event registration state machine."""
    
    def test_registration_workflow(self, app, volunteer_user, event):
        """Test full registration workflow: pending → approved → attended."""
        with app.app_context():
            admin = User.query.filter_by(role='admin').first()
            
            # Volunteer registers
            reg = EventRegistration(
                volunteer_id=volunteer_user.id,
                event_id=event.id,
                registration_status=EventRegistration.STATUS_PENDING
            )
            db.session.add(reg)
            db.session.commit()
            
            assert reg.registration_status == EventRegistration.STATUS_PENDING
            
            # Admin approves
            reg.approve(admin.id, 'Approved')
            assert reg.registration_status == EventRegistration.STATUS_APPROVED
            assert reg.approved_by == admin.id
            
            # Volunteer attends
            reg.mark_attended()
            assert reg.registration_status == EventRegistration.STATUS_ATTENDED


class TestAttendanceTracking:
    """Test attendance check-in/check-out."""
    
    def test_check_in_check_out(self, app, volunteer_user, event):
        """Test volunteer check-in and check-out."""
        from datetime import datetime, timedelta
        
        with app.app_context():
            check_in = datetime.utcnow()
            check_out = check_in + timedelta(hours=3)
            
            attendance = Attendance(
                volunteer_id=volunteer_user.id,
                event_id=event.id,
                check_in_time=check_in,
                qr_code=Attendance.generate_qr_code(),
                status=Attendance.STATUS_CHECKED_IN
            )
            db.session.add(attendance)
            db.session.commit()
            
            # Initially checked in
            assert attendance.status == Attendance.STATUS_CHECKED_IN
            assert attendance.hours_served is None
            
            # Later: Check out
            attendance.check_out_time = check_out
            attendance.check_out()
            
            assert attendance.status == Attendance.STATUS_CHECKED_OUT
            assert attendance.hours_served == 3.0  # 3 hours


class TestCertificateGeneration:
    """Test certificate issuance."""
    
    def test_create_attendance_certificate(self, app, volunteer_user, event):
        """Test creating attendance certificate."""
        with app.app_context():
            cert = Certificate.create_attendance_certificate(
                volunteer_user,
                event,
                hours=4.0
            )
            
            assert cert.volunteer_id == volunteer_user.id
            assert cert.event_id == event.id
            assert cert.certificate_type == Certificate.TYPE_ATTENDANCE
            assert cert.verification_code is not None
            assert len(cert.verification_code) > 0


class TestDonationTracking:
    """Test donation management."""
    
    def test_create_donation(self, app, volunteer_user):
        """Test creating a donation."""
        from decimal import Decimal
        
        with app.app_context():
            donation = Donation(
                volunteer_id=volunteer_user.id,
                amount=Decimal('500.00'),
                currency='INR',
                donation_status=Donation.STATUS_PENDING
            )
            db.session.add(donation)
            db.session.commit()
            
            assert donation.id is not None
            assert float(donation.amount) == 500.0
            assert donation.donation_status == Donation.STATUS_PENDING
    
    def test_donation_verification(self, app, volunteer_user):
        """Test admin verifies donation."""
        from decimal import Decimal
        
        with app.app_context():
            admin = User.query.filter_by(role='admin').first()
            
            donation = Donation(
                volunteer_id=volunteer_user.id,
                amount=Decimal('1000.00'),
                currency='INR'
            )
            db.session.add(donation)
            db.session.commit()
            
            donation.verify(admin.id)
            
            assert donation.donation_status == Donation.STATUS_VERIFIED
            assert donation.verified_by == admin.id
            assert donation.verified_at is not None


# Run tests with: pytest tests/test_models.py -v