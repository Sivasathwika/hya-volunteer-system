"""
Base configuration for HYA Volunteer Management System.
This file contains settings shared across all environments.
Environment-specific overrides go in development.py, production.py, etc.
"""

import os
from datetime import timedelta

# Flask Core Settings
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = False
TESTING = False

# Database
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False  # Set to True to see SQL queries in logs

# Session Management
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
SESSION_COOKIE_SECURE = False  # Set to True in production (HTTPS only)
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

# JWT Authentication
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# File Upload
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Pagination
ITEMS_PER_PAGE = 20

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/app.log'

# Application Settings
APP_NAME = 'HYA Volunteer Management System'
APP_VERSION = '1.0.0'

# Email Configuration (for future notifications)
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@hya.org')