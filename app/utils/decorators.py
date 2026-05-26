"""
Custom decorators for route protection.

Why decorators?
- @login_required: Only logged-in users can access
- @admin_only: Only admins can access
- @volunteer_only: Only volunteers can access
- Reusable: Apply to any route

Design:
- Stack decorators: @app.route(...) @login_required @admin_only def route()
- Order matters: login_required should be above role-specific decorators
"""

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def login_required_custom(f):
    """
    Decorator to require user to be logged in.
    
    Usage:
        @app.route('/dashboard')
        @login_required_custom
        def dashboard():
            return render_template('dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_only(f):
    """
    Decorator to require admin role.
    
    Should be used with @login_required or @login_required_custom.
    
    Usage:
        @app.route('/admin/users')
        @login_required_custom
        @admin_only
        def manage_users():
            return render_template('admin/users.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('volunteer.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def volunteer_only(f):
    """
    Decorator to require volunteer role.
    
    Usage:
        @app.route('/volunteer/profile')
        @login_required_custom
        @volunteer_only
        def volunteer_profile():
            return render_template('volunteer/profile.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_volunteer():
            flash('This page is for volunteers only', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Decorator to require one of multiple roles.
    
    More flexible version of admin_only/volunteer_only.
    
    Usage:
        @app.route('/special-page')
        @role_required('admin', 'volunteer')
        def special_page():
            return render_template('special.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login first', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('volunteer.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator