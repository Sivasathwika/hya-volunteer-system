"""
Configuration loader - selects config based on FLASK_ENV environment variable.
"""

import os

# Determine which config to load based on environment
env = os.getenv('FLASK_ENV', 'development').lower()

if env == 'production':
    from config.production import *
elif env == 'testing':
    from config.testing import *
else:
    from config.development import *

__all__ = ['env']