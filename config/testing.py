"""
Testing configuration - Uses in-memory SQLite for fast tests.
"""

from config.default import *

# Use in-memory database for tests (fast, isolated)
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Enable testing mode
TESTING = True
DEBUG = True

# Disable CSRF for testing
WTF_CSRF_ENABLED = False

# Disable email sending in tests
MAIL_SUPPRESS_SEND = True

print("✓ Using TESTING configuration")