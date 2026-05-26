"""
Development configuration for local testing.
Uses SQLite for simplicity, enables debug mode and verbose output.
"""

from config.default import *
import os

# Override default settings for development

# Use SQLite for local development (no PostgreSQL setup needed)
SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URL',
    'sqlite:///hya_development.db'
)

# Enable debug mode for auto-reload and detailed error pages
DEBUG = True
TESTING = False

# Show SQL queries in console for debugging
SQLALCHEMY_ECHO = True

# Disable session cookie security for local testing
SESSION_COOKIE_SECURE = False

# Verbose logging
LOG_LEVEL = 'DEBUG'

# Disable email sending in development
MAIL_SUPPRESS_SEND = True

print("✓ Using DEVELOPMENT configuration")
print(f"  Database: {SQLALCHEMY_DATABASE_URI}")
print(f"  Debug Mode: {DEBUG}")