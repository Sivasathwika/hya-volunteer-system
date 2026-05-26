"""
Authentication service - Business logic layer.

Why separate service layer?
- Routes are thin (accept input, call service, return response)
- Services contain business logic (can be tested independently)
- Easy to reuse logic (same registration logic from API or web form)
- Easy to test (mock the service, not the whole route)

Design:
- register_user(): Validate email, create user, hash password
- login_user(): Verify credentials, return user or error
- change_password(): Verify old password, set new password
"""

import logging
from app.database import db
from app.models import User, Volunteer

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication business logic."""
    
    @staticmethod
    def register_user(email: str, password: str, first_name: str, last_name: str,
                      role: str = 'volunteer', phone: str = None) -> dict:
        """
        Register a new user.
        
        Args:
            email: User's email (must be unique)
            password: Plain text password (will be hashed)
            first_name: User's first name
            last_name: User's last name
            role: 'admin' or 'volunteer' (default: volunteer)
            phone: Optional phone number
        
        Returns:
            dict with 'success' (bool) and 'message' (str)
            If success: {'success': True, 'user': User instance}
            If error: {'success': False, 'message': error reason}
        """
        
        # Validate email format
        if not User.validate_email(email):
            return {
                'success': False,
                'message': 'Invalid email format'
            }
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email.lower()).first()
        if existing_user:
            logger.warning(f"Registration attempt with duplicate email: {email}")
            return {
                'success': False,
                'message': 'Email already registered'
            }
        
        # Validate role
        if role not in User.VALID_ROLES:
            return {
                'success': False,
                'message': f'Invalid role. Must be {", ".join(User.VALID_ROLES)}'
            }
        
        try:
            # Create user based on role
            if role == 'volunteer':
                user = Volunteer(
                    email=email.lower(),
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role=role,
                    is_active=True
                )
            else:
                user = User(
                    email=email.lower(),
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role=role,
                    is_active=True
                )
            
            # Set password (will be hashed)
            user.set_password(password)
            
            # Save to database
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {email} ({role})")
            
            return {
                'success': True,
                'message': f'Account created successfully. Please login.',
                'user': user
            }
        
        except ValueError as e:
            # Password strength validation failed
            db.session.rollback()
            logger.error(f"Password validation failed for {email}: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
        
        except Exception as e:
            # Unexpected error
            db.session.rollback()
            logger.exception(f"Error during registration: {str(e)}")
            return {
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }
    
    @staticmethod
    def login_user(email: str, password: str) -> dict:
        """
        Authenticate user credentials.
        
        Args:
            email: User's email
            password: Plain text password (will be verified against hash)
        
        Returns:
            dict with 'success' (bool) and 'message' (str)
            If success: {'success': True, 'user': User instance}
            If error: {'success': False, 'message': error reason}
        """
        
        # Find user by email
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return {
                'success': False,
                'message': 'Invalid email or password'  # Don't reveal if email exists
            }
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt on deactivated account: {email}")
            return {
                'success': False,
                'message': 'This account has been deactivated. Contact support.'
            }
        
        # Verify password
        if not user.check_password(password):
            logger.warning(f"Failed login attempt for {email} (wrong password)")
            return {
                'success': False,
                'message': 'Invalid email or password'
            }
        
        logger.info(f"User logged in: {email}")
        
        return {
            'success': True,
            'message': 'Login successful',
            'user': user
        }
    
    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> dict:
        """
        Change user's password.
        
        Args:
            user: User instance
            current_password: Current password (for verification)
            new_password: New password (will be hashed)
        
        Returns:
            dict with 'success' and 'message'
        """
        
        # Verify current password
        if not user.check_password(current_password):
            logger.warning(f"Password change attempt with wrong current password: {user.email}")
            return {
                'success': False,
                'message': 'Current password is incorrect'
            }
        
        try:
            # Set new password (will be validated and hashed)
            user.set_password(new_password)
            db.session.commit()
            
            logger.info(f"Password changed for user: {user.email}")
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
        
        except ValueError as e:
            db.session.rollback()
            return {
                'success': False,
                'message': str(e)
            }
        
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error changing password: {str(e)}")
            return {
                'success': False,
                'message': 'An unexpected error occurred'
            }
    
    @staticmethod
    def logout_user(user: User) -> dict:
        """
        Logout user (mainly for logging).
        
        Args:
            user: User instance being logged out
        
        Returns:
            dict with success message
        """
        logger.info(f"User logged out: {user.email}")
        return {
            'success': True,
            'message': 'Logged out successfully'
        }