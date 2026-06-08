"""
Production-specific settings
"""

from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# AWS S3 Storage (for production media files)
USE_S3 = config('USE_S3', default=False, cast=bool)
if USE_S3:
    # DigitalOcean Spaces (S3-compatible)
    AWS_ACCESS_KEY_ID = config('SPACES_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = config('SPACES_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = config('SPACES_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('SPACES_REGION', default='lon1')
    AWS_S3_ENDPOINT_URL = f'https://{AWS_S3_REGION_NAME}.digitaloceanspaces.com'
    AWS_S3_CUSTOM_DOMAIN = config(
        'SPACES_CDN_ENDPOINT',
        default=f'{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_REGION_NAME}.digitaloceanspaces.com'
    )
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_DEFAULT_ACL = 'public-read'
    AWS_LOCATION = 'media'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Sentry Error Tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# In production, log to console only (Docker captures stdout)
LOGGING['handlers']['file']['filename'] = str(BASE_DIR / 'logs' / 'django.log')
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)