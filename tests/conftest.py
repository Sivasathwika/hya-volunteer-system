"""
Pytest configuration and fixtures.

Fixtures provide:
- Test client for making HTTP requests
- Database with clean state for each test
- Sample data for testing
"""

import pytest
from app import create_app, db
from app.models import User, Volunteer, Event, Skill


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.create_all()
        yield app
        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner for testing commands."""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Create a test admin user."""
    with app.app_context():
        admin = User(
            email='admin@hya.org',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def volunteer_user(app):
    """Create a test volunteer user."""
    with app.app_context():
        volunteer = Volunteer(
            email='volunteer@hya.org',
            first_name='John',
            last_name='Volunteer',
            role='volunteer',
            is_active=True,
            city='Hyderabad',
            state='Telangana'
        )
        volunteer.set_password('Volunteer@123')
        db.session.add(volunteer)
        db.session.commit()
        return volunteer


@pytest.fixture
def event(app, admin_user):
    """Create a test event."""
    with app.app_context():
        from datetime import date, time
        event = Event(
            title='Park Cleanup',
            description='Clean up the local park',
            event_date=date(2024, 12, 25),
            start_time=time(9, 0),
            end_time=time(12, 0),
            location='Central Park',
            capacity=50,
            created_by=admin_user.id,
            status='published'
        )
        db.session.add(event)
        db.session.commit()
        return event


@pytest.fixture
def skill(app):
    """Create a test skill."""
    with app.app_context():
        skill = Skill(
            name='Python',
            category='Programming'
        )
        db.session.add(skill)
        db.session.commit()
        return skill