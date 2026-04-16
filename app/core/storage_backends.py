from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'


class MediaStorage(S3Boto3Storage):
    location = getattr(settings, 'MEDIA_LOCATION', 'media')
    default_acl = getattr(settings, 'AWS_DEFAULT_ACL', 'public-read')
    file_overwrite = False
