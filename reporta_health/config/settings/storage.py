from decouple import config

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

STORAGE_BACKEND = config('STORAGE_BACKEND', default='local')  # 'local', 'supabase', 'digitalocean'

if STORAGE_BACKEND == 'supabase':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = config('SUPABASE_S3_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = config('SUPABASE_S3_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = config('SUPABASE_BUCKET_NAME', default='reporta-health')
    AWS_S3_ENDPOINT_URL = f"{config('SUPABASE_URL')}/storage/v1/s3"
    AWS_S3_REGION_NAME = 'us-east-1'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    MEDIA_URL = f"{config('SUPABASE_URL')}/storage/v1/object/public/{config('SUPABASE_BUCKET_NAME', default='reporta-health')}/"

elif STORAGE_BACKEND == 'digitalocean':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = config('DO_SPACES_KEY')
    AWS_SECRET_ACCESS_KEY = config('DO_SPACES_SECRET')
    AWS_STORAGE_BUCKET_NAME = config('DO_SPACES_BUCKET')
    AWS_S3_ENDPOINT_URL = config('DO_SPACES_ENDPOINT')  # e.g. https://nyc3.digitaloceanspaces.com
    AWS_S3_REGION_NAME = config('DO_SPACES_REGION', default='nyc3')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    MEDIA_URL = f"{config('DO_SPACES_ENDPOINT')}/{config('DO_SPACES_BUCKET')}/"

else:  # local
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'