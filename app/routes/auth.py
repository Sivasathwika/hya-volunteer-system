"""
Authentication routes - Flask Blueprint.

Routes:
- GET /auth/register → Show registration form
- POST /auth/register → Process registration
- GET /auth/login → Show login form
- POST /auth/login → Process login
- GET /auth/logout → Logout and redirect

Design:
- Thin routes: Accept input, validate with forms, call service, return response
- Services contain business logic
- Forms contain input validation
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.forms.auth_forms import RegistrationForm, LoginForm
from app.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration page.
    
    GET: Show registration form
    POST: Process registration form
    """
    
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('volunteer.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Form validation passed, process registration
        result = AuthService.register_user(
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
            phone=form.phone.data if form.phone.data else None
        )
        
        if result['success']:
            flash(result['message'], 'success')
            logger.info(f"User registered successfully: {form.email.data}")
            return redirect(url_for('auth.login'))
        else:
            flash(result['message'], 'danger')
            logger.warning(f"Registration failed: {result['message']}")
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.
    
    GET: Show login form
    POST: Process login form
    """
    
    # Redirect if already logged in
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('volunteer.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Form validation passed, authenticate user
        result = AuthService.login_user(
            email=form.email.data,
            password=form.password.data
        )
        
        if result['success']:
            user = result['user']
            # Create session
            login_user(user, remember=form.remember_me.data)
            
            flash(f"Welcome back, {user.first_name}!", 'success')
            logger.info(f"User logged in: {form.email.data}")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('volunteer.dashboard'))
        else:
            flash(result['message'], 'danger')
            logger.warning(f"Login failed for {form.email.data}")
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """
    Logout current user.
    
    Destroys session and redirects to home.
    """
    
    if current_user.is_authenticated:
        AuthService.logout_user(current_user)
        logout_user()
        flash('You have been logged out successfully', 'info')
    
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """
    Change password page (requires login).
    
    GET: Show change password form
    POST: Process change password form
    """
    from flask_login import login_required
    from app.forms.auth_forms import ChangePasswordForm
    
    @login_required
    def _change_password():
        form = ChangePasswordForm()
        
        if form.validate_on_submit():
            result = AuthService.change_password(
                user=current_user,
                current_password=form.current_password.data,
                new_password=form.new_password.data
            )
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('volunteer.dashboard'))
            else:
                flash(result['message'], 'danger')
        
        return render_template('auth/change_password.html', form=form)
    
    return _change_password()