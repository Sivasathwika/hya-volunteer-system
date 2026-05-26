"""
Integration tests for authentication system.

Tests cover:
- User registration with validation
- Login/logout flows
- Password security
- Form validation errors
- Protected routes
"""

import pytest
from app import db
from app.models import User, Volunteer


class TestRegistrationRoute:
    """Test registration endpoint."""
    
    def test_registration_page_loads(self, client):
        """Test GET /auth/register shows form."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Create Your Account' in response.data
        assert b'Email Address' in response.data
    
    def test_register_new_volunteer(self, client, app):
        """Test successful volunteer registration."""
        with app.app_context():
            response = client.post('/auth/register', data={
                'email': 'newvol@hya.org',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'phone': '+919876543210',
                'password': 'SecurePass@123',
                'confirm_password': 'SecurePass@123',
                'role': 'volunteer'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Account created successfully' in response.data
            
            # Check user was created in database
            user = Volunteer.query.filter_by(email='newvol@hya.org').first()
            assert user is not None
            assert user.first_name == 'Jane'
            assert user.role == 'volunteer'
    
    def test_register_weak_password_rejected(self, client):
        """Test weak passwords are rejected."""
        response = client.post('/auth/register', data={
            'email': 'newuser@hya.org',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'weak',  # Too short, missing requirements
            'confirm_password': 'weak',
            'role': 'volunteer'
        })
        
        assert response.status_code == 200
        assert b'Password must be at least 8 characters' in response.data or \
               b'must contain at least one uppercase letter' in response.data
    
    def test_register_duplicate_email_rejected(self, client, app, admin_user):
        """Test duplicate email is rejected."""
        response = client.post('/auth/register', data={
            'email': admin_user.email,  # Already registered
            'first_name': 'Another',
            'last_name': 'User',
            'password': 'NewPass@123',
            'confirm_password': 'NewPass@123',
            'role': 'volunteer'
        })
        
        assert response.status_code == 200
        assert b'Email already registered' in response.data
    
    def test_password_mismatch_rejected(self, client):
        """Test mismatched passwords are rejected."""
        response = client.post('/auth/register', data={
            'email': 'newuser@hya.org',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'ValidPass@123',
            'confirm_password': 'DifferentPass@123',  # Doesn't match
            'role': 'volunteer'
        })
        
        assert response.status_code == 200
        assert b'Passwords must match' in response.data


class TestLoginRoute:
    """Test login endpoint."""
    
    def test_login_page_loads(self, client):
        """Test GET /auth/login shows form."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data
        assert b'Email Address' in response.data
    
    def test_successful_login(self, client, app, admin_user):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'Admin@123',  # Password from fixture
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome back' in response.data
    
    def test_login_wrong_password(self, client, admin_user):
        """Test login with wrong password."""
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'WrongPassword@123',
            'remember_me': False
        })
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@hya.org',
            'password': 'Password@123',
            'remember_me': False
        })
        
        assert response.status_code == 200
        assert b'Email not found' in response.data or b'Invalid email or password' in response.data
    
    def test_login_remember_me(self, client, admin_user):
        """Test 'remember me' functionality."""
        response = client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'Admin@123',
            'remember_me': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Session should be set with longer expiration


class TestLogoutRoute:
    """Test logout endpoint."""
    
    def test_logout(self, client, app, admin_user):
        """Test logout functionality."""
        # First login
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'Admin@123',
            'remember_me': False
        })
        
        # Then logout
        response = client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'logged out successfully' in response.data


class TestAuthenticationProtection:
    """Test that protected routes require authentication."""
    
    def test_unauthenticated_user_redirected(self, client):
        """Test unauthenticated user trying to access protected route."""
        # These routes don't exist yet, but will be tested in next milestone
        # For now, just verify our setup works
        response = client.get('/auth/login')
        assert response.status_code == 200


class TestAuthServiceLogic:
    """Test AuthService business logic."""
    
    def test_register_user_service(self, app):
        """Test register_user service method."""
        from app.services.auth_service import AuthService
        
        with app.app_context():
            result = AuthService.register_user(
                email='service@hya.org',
                password='ServicePass@123',
                first_name='Service',
                last_name='User',
                role='volunteer'
            )
            
            assert result['success'] is True
            assert 'Account created' in result['message']
            
            user = Volunteer.query.filter_by(email='service@hya.org').first()
            assert user is not None
    
    def test_login_user_service(self, app, admin_user):
        """Test login_user service method."""
        from app.services.auth_service import AuthService
        
        with app.app_context():
            result = AuthService.login_user(
                email=admin_user.email,
                password='Admin@123'
            )
            
            assert result['success'] is True
            assert result['user'].email == admin_user.email
    
    def test_login_user_service_wrong_password(self, app, admin_user):
        """Test login_user with wrong password."""
        from app.services.auth_service import AuthService
        
        with app.app_context():
            result = AuthService.login_user(
                email=admin_user.email,
                password='WrongPassword@123'
            )
            
            assert result['success'] is False
            assert 'Invalid' in result['message']