"""
WTForms for authentication.

Why WTForms?
- Validates input before database operations
- CSRF protection (hidden token on every form)
- Consistent error messages
- Easy to customize validation
- Works seamlessly with Flask

Design:
- RegistrationForm: Email, password, confirm password, name
- LoginForm: Email, password
- Custom validators for strong passwords
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, 
    ValidationError, Regexp
)
from app.models import User


class RegistrationForm(FlaskForm):
    """
    Registration form for new users (both admin and volunteer).
    
    Fields:
    - email: Unique email address
    - first_name: First name
    - last_name: Last name
    - phone: Optional phone number
    - password: Must be 8+ chars with uppercase, number, special char
    - confirm_password: Must match password
    - role: Select 'admin' or 'volunteer'
    """
    
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Invalid email address')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'name@example.com'}
    )
    
    first_name = StringField(
        'First Name',
        validators=[
            DataRequired(message='First name is required'),
            Length(min=2, max=100, message='First name must be 2-100 characters')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'John'}
    )
    
    last_name = StringField(
        'Last Name',
        validators=[
            DataRequired(message='Last name is required'),
            Length(min=2, max=100, message='Last name must be 2-100 characters')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'Doe'}
    )
    
    phone = StringField(
        'Phone Number (Optional)',
        validators=[
            Length(min=0, max=20, message='Phone must be 20 characters or less')
        ],
        render_kw={'class': 'form-control', 'placeholder': '+91 9876543210'}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(
                min=8,
                message='Password must be at least 8 characters'
            ),
            Regexp(
                r'(?=.*[A-Z])',
                message='Password must contain at least one uppercase letter'
            ),
            Regexp(
                r'(?=.*[0-9])',
                message='Password must contain at least one number'
            ),
            Regexp(
                r'(?=.*[!@#$%^&*()_+\-=\[\]{}|;:,.<>?])',
                message='Password must contain at least one special character (!@#$%^&*)'
            )
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Password@123'
        }
    )
    
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Password@123'
        }
    )
    
    role = SelectField(
        'Registration Type',
        choices=[('volunteer', 'Volunteer'), ('admin', 'Admin')],
        default='volunteer',
        validators=[DataRequired()],
        render_kw={'class': 'form-control'}
    )
    
    submit = SubmitField(
        'Create Account',
        render_kw={'class': 'btn btn-primary w-100'}
    )
    
    def validate_email(self, email):
        """
        Custom validator: Check if email already exists.
        WTForms calls this automatically before form validation completes.
        """
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError(
                'Email already registered. Please login or use a different email.'
            )


class LoginForm(FlaskForm):
    """
    Login form for existing users.
    
    Fields:
    - email: User's email
    - password: User's password
    - remember_me: Keep me logged in for 30 days
    """
    
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Invalid email address')
        ],
        render_kw={'class': 'form-control', 'placeholder': 'name@example.com'}
    )
    
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required')],
        render_kw={'class': 'form-control', 'placeholder': 'Password@123'}
    )
    
    remember_me = BooleanField(
        'Keep me logged in',
        render_kw={'class': 'form-check-input'}
    )
    
    submit = SubmitField(
        'Sign In',
        render_kw={'class': 'btn btn-primary w-100'}
    )
    
    def validate_email(self, email):
        """
        Custom validator: Check if user exists.
        Gives hint to user if email not found.
        """
        user = User.query.filter_by(email=email.data.lower()).first()
        if not user:
            raise ValidationError(
                'Email not found. Please register first.'
            )


class ChangePasswordForm(FlaskForm):
    """
    Form for changing password while logged in.
    
    Requires:
    - Current password (to verify identity)
    - New password (with strength requirements)
    - Confirm new password
    """
    
    current_password = PasswordField(
        'Current Password',
        validators=[DataRequired(message='Current password is required')],
        render_kw={'class': 'form-control'}
    )
    
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='New password is required'),
            Length(min=8, message='Password must be at least 8 characters'),
            Regexp(
                r'(?=.*[A-Z])',
                message='Password must contain at least one uppercase letter'
            ),
            Regexp(
                r'(?=.*[0-9])',
                message='Password must contain at least one number'
            ),
            Regexp(
                r'(?=.*[!@#$%^&*()_+\-=\[\]{}|;:,.<>?])',
                message='Password must contain at least one special character'
            )
        ],
        render_kw={'class': 'form-control'}
    )
    
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm new password'),
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={'class': 'form-control'}
    )
    
    submit = SubmitField(
        'Change Password',
        render_kw={'class': 'btn btn-primary'}
    )