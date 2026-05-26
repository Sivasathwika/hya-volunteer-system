"""
Flask application factory.

App factory pattern:
- Allows creating multiple app instances with different configs
- Enables testing with different configurations
- Keeps app creation logic centralized

Why not create Flask app at module level?
- Can't pass config at creation time
- Circular import issues
- Can't run tests with test config
"""

from flask import Flask
from flask_login import LoginManager
from app.database import init_db, db
import logging
import os


def create_app(config_name=None):
    """
    Application factory - Creates and configures Flask app.
    
    Args:
        config_name: 'development', 'production', or 'testing'
                     If None, uses FLASK_ENV environment variable
    
    Returns:
        Configured Flask application instance
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    if config_name == 'production':
        app.config.from_object('config.production')
    elif config_name == 'testing':
        app.config.from_object('config.testing')
    else:
        app.config.from_object('config.development')
    
    # Initialize database
    init_db(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints (routes)
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def setup_logging(app):
    """Configure application logging."""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # File handler
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('HYA Volunteer Management System started')


def register_blueprints(app):
    """Register Flask blueprints (routes)."""
    
    from app.routes.auth import auth_bp
    from app.routes.volunteer import volunteer_bp
    from app.routes.admin import admin_bp
    from app.routes.events import events_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(volunteer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(events_bp)


def register_error_handlers(app):
    """Register error handlers for common HTTP errors."""
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }, 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return {
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }, 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }, 500