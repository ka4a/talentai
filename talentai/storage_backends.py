from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'
    querystring_auth = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # to avoid 307 redirect that slows down browser caching
        self.custom_domain = (
            f'{settings.AWS_STORAGE_BUCKET_NAME}'
            f'.s3-{settings.AWS_S3_REGION_NAME}.amazonaws.com'
        )
