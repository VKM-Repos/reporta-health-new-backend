"""
Test settings for Reporta Health
Inherits from base, overrides for fast isolated testing
"""
import os
from config.settings.base import *  # noqa

# Use a separate test database
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'reporta_health_test',
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'TEST': {
            'NAME': 'reporta_health_test',
        },
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable real email sending
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use in-memory cache (no Redis dependency in tests)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',  # was LocMemCache

    }
}



# Disable all throttling in tests — rate limits have no place in a test suite
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [],
    # 'DEFAULT_THROTTLE_RATES': {},
}

# Disable Celery — tasks run synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Silence logging noise during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {'class': 'logging.NullHandler'},
    },
    'root': {
        'handlers': ['null'],
    },
}

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

MEDIA_ROOT = '/tmp/reporta_test_media/'

DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'test-secret-key-not-for-production')