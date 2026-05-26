"""
Integration tests for volunteer, admin, and event routes.

Tests cover:
- Route access control (login required, role-based)
- Volunteer dashboard and profile
- Admin dashboard and event management
- Event listing and registration
"""

import pytest
from datetime import date, time, timedelta
from app import db
from app.models import Event, EventRegistration, Volunteer


class TestVolunteerRoutes:
    """Test volunteer-only routes."""
    
    def test_volunteer_dashboard_requires_login(self, client):
        """Test that volunteer dashboard requires login."""
        response = client.get('/volunteer/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_volunteer_dashboard_accessible_to_volunteer(self, client, app, volunteer_user):
        """Test volunteer can access their dashboard."""
        with app.app_context():
            client.post('/auth/login', data={
                'email': volunteer_user.email,
                'password': 'Volunteer@123',
                'remember_me': False
            })
        
        response = client.get('/volunteer/dashboard')
        assert response.status_code == 200
        assert b'Welcome' in response.data
    
    def test_volunteer_profile_page_loads(self, client, app, volunteer_user):
        """Test volunteer profile page."""
        with app.app_context():
            client.post('/auth/login', data={
                'email': volunteer_user.email,
                'password': 'Volunteer@123',
                'remember_me': False
            })
        
        response = client.get('/volunteer/profile')
        assert response.status_code == 200
    
    def test_volunteer_update_profile(self, client, app, volunteer_user):
        """Test updating volunteer profile."""
        with app.app_context():
            client.post('/auth/login', data={
                'email': volunteer_user.email,
                'password': 'Volunteer@123',
                'remember_me': False
            })
        
        response = client.post('/volunteer/profile', data={
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '9876543210',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'bio': 'Updated bio'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Profile updated' in response.data
        
        # Verify update in database
        with app.app_context():
            vol = Volunteer.query.filter_by(email=volunteer_user.email).first()
            assert vol.city == 'Bangalore'
            assert vol.state == 'Karnataka'


class TestAdminRoutes:
    """Test admin-only routes."""
    
    def test_admin_dashboard_requires_admin_role(self, client, app, volunteer_user):
        """Test that non-admins cannot access admin dashboard."""
        with app.app_context():
            client.post('/auth/login', data={
                'email': volunteer_user.email,
                'password': 'Volunteer@123',
                'remember_me': False
            })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 302  # Redirect
    
    def test_admin_dashboard_accessible_to_admin(self, client, app, admin_user):
        """Test admin can access admin dashboard."""
        with app.app_context():
            client.post('/auth/login', data={
                'email': admin_user.email,
                'password': 'Admin@123',
                'remember_me': False
            })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
    
    def test_admin_create_event(self, client, app, admin_user):
        """Test admin can create event."""
        with app.app_context():
            client.post('/auth/login', data={
                'email': admin_user.email,
                'password': 'Admin@123',
                'remember_me': False
            })
        
        future_date = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        response = client.post('/admin/events/create', data={
            'title': 'Beach Cleanup',
            'description': 'Clean up the beach',
            'event_date': future_date,
            'start_time': '09:00',
            'end_time': '12:00',
            'location': 'Marina Beach',
            'capacity': 50
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully' in response.data or b'Beach Cleanup' in response.data
    
    def test_admin_view_volunteers(self, client, app, admin_user):
        """Test admin can view list of volunteers."""
        with app.app_context():
            client.post('/auth/login', data={
                'email': admin_user.email,
                'password': 'Admin@123',
                'remember_me': False
            })
        
        response = client.get('/admin/volunteers')
        assert response.status_code == 200


class TestEventRoutes:
    """Test event listing and registration."""
    
    def test_event_list_public(self, client, app, event):
        """Test event listing is public (no login required)."""
        response = client.get('/events/')
        assert response.status_code == 200
        # Note: Event might not show if it's in draft status
    
    def test_event_detail_page(self, client, event):
        """Test event detail page."""
        response = client.get(f'/events/{event.id}')
        assert response.status_code == 200
    
    def test_volunteer_register_for_event(self, client, app, volunteer_user, event):
        """Test volunteer can register for event."""
        with app.app_context():
            # First publish the event
            event.publish()
            db.session.commit()
            
            client.post('/auth/login', data={
                'email': volunteer_user.email,
                'password': 'Volunteer@123',
                'remember_me': False
            })
        
        response = client.post(
            f'/events/{event.id}/register',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'registered' in response.data.lower() or b'pending' in response.data.lower()
        
        # Verify registration in database
        with app.app_context():
            registration = EventRegistration.query.filter_by(
                volunteer_id=volunteer_user.id,
                event_id=event.id
            ).first()
            assert registration is not None
            assert registration.registration_status == EventRegistration.STATUS_PENDING
    
    def test_cannot_register_twice(self, client, app, volunteer_user, event):
        """Test volunteer cannot register twice for same event."""
        with app.app_context():
            event.publish()
            
            # Create first registration
            reg = EventRegistration(
                volunteer_id=volunteer_user.id,
                event_id=event.id,
                registration_status=EventRegistration.STATUS_PENDING
            )
            db.session.add(reg)
            db.session.commit()
            
            client.post('/auth/login', data={
                'email': volunteer_user.email,
                'password': 'Volunteer@123',
                'remember_me': False
            })
        
        # Try to register again
        response = client.post(
            f'/events/{event.id}/register',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'already registered' in response.data.lower()
    
    def test_volunteer_unregister_event(self, client, app, volunteer_user, event):
        """Test volunteer can unregister from event."""
        with app.app_context():
            event.publish()
            
            # Create registration
            reg = EventRegistration(
                volunteer_id=volunteer_user.id,
                event_id=event.id,
                registration_status=EventRegistration.STATUS_PENDING
            )
            db.session.add(reg)
            db.session.commit()
            
            client.post('/auth/login', data={
                'email': volunteer_user.email,
                'password': 'Volunteer@123',
                'remember_me': False
            })
        
        response = client.post(
            f'/events/{event.id}/unregister',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'cancelled' in response.data.lower()
        
        # Verify registration deleted
        with app.app_context():
            registration = EventRegistration.query.filter_by(
                volunteer_id=volunteer_user.id,
                event_id=event.id
            ).first()
            assert registration is None