"""
Production configuration for Render deployment.
Uses PostgreSQL, enables security features, disables debug mode.
"""

from config.default import *
import os

# Override default settings for production

# Use PostgreSQL in production (provided by Render)
SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/hya_production'
)

# Disable debug mode (never in production!)
DEBUG = False
TESTING = False

# Hide SQL queries for performance
SQLALCHEMY_ECHO = False

# Enable security headers
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# Minimal logging (only errors)
LOG_LEVEL = 'ERROR'

# Enable email notifications in production
MAIL_SUPPRESS_SEND = False

# Enforce HTTPS redirects
PREFER_HTTPS = True

print("✓ Using PRODUCTION configuration")
print(f"  Database: PostgreSQL (configured via DATABASE_URL)")
print(f"  Debug Mode: {DEBUG}")
print(f"  HTTPS Enforced: {SESSION_COOKIE_SECURE}")