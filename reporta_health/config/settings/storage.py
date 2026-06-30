from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

STORAGE_BACKEND = config('STORAGE_BACKEND', default='local')


if STORAGE_BACKEND == 'supabase':
    from storages.backends.s3boto3 import S3Boto3Storage

    AWS_ACCESS_KEY_ID = config('SUPABASE_S3_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = config('SUPABASE_S3_SECRET_KEY')
    AWS_S3_ENDPOINT_URL = f"{config('SUPABASE_URL')}/storage/v1/s3"
    AWS_S3_REGION_NAME = 'us-east-1'
    AWS_QUERYSTRING_AUTH = False

    class FacilitiesStorage(S3Boto3Storage):
        bucket_name = 'facilities'
        default_acl = 'public-read'

    class ReportsStorage(S3Boto3Storage):
        bucket_name = 'reports'
        default_acl = 'private'

    class AvatarsStorage(S3Boto3Storage):
        bucket_name = 'avatars'
        default_acl = 'public-read'

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

elif STORAGE_BACKEND == 'digitalocean':
    from storages.backends.s3boto3 import S3Boto3Storage

    AWS_ACCESS_KEY_ID = config('DO_SPACES_KEY')
    AWS_SECRET_ACCESS_KEY = config('DO_SPACES_SECRET')
    AWS_S3_ENDPOINT_URL = config('DO_SPACES_ENDPOINT')
    AWS_S3_REGION_NAME = config('DO_SPACES_REGION', default='nyc3')
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = 'public-read'

    class FacilitiesStorage(S3Boto3Storage):
        bucket_name = config('DO_SPACES_BUCKET')
        location = 'facilities'
        default_acl = 'public-read'

    class ReportsStorage(S3Boto3Storage):
        bucket_name = config('DO_SPACES_BUCKET')
        location = 'reports'
        default_acl = 'private'

    class AvatarsStorage(S3Boto3Storage):
        bucket_name = config('DO_SPACES_BUCKET')
        location = 'avatars'
        default_acl = 'public-read'

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

else:  # local
    from django.core.files.storage import FileSystemStorage

    class FacilitiesStorage(FileSystemStorage):
        location = 'media/facilities'
        base_url = '/media/facilities/'

    class ReportsStorage(FileSystemStorage):
        location = 'media/reports'
        base_url = '/media/reports/'

    class AvatarsStorage(FileSystemStorage):
        location = 'media/avatars'
        base_url = '/media/avatars/'

    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'