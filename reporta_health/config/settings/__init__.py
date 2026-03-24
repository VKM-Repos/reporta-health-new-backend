"""
Automatically load the correct settings module based on environment
"""

import os

# Default to development settings
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .production import *  # Use production settings for staging
else:
    from .development import *