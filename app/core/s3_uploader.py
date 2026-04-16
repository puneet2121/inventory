import mimetypes
import os
from uuid import uuid4
from urllib.parse import quote

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from django.conf import settings


class S3UploadError(Exception):
    pass


def _client():
    bucket = getattr(settings, 'S3_UPLOAD_BUCKET', None)
    if not bucket:
        raise S3UploadError("S3 upload bucket is not configured")

    session = boto3.session.Session(region_name=getattr(settings, 'S3_UPLOAD_REGION', None))
    client_kwargs = {
        'service_name': 's3',
        'endpoint_url': getattr(settings, 'S3_UPLOAD_ENDPOINT', None),
        'aws_access_key_id': getattr(settings, 'S3_UPLOAD_ACCESS_KEY', None),
        'aws_secret_access_key': getattr(settings, 'S3_UPLOAD_SECRET_KEY', None),
    }

    if getattr(settings, 'S3_UPLOAD_USE_ANONYMOUS', False):
        client_kwargs['config'] = Config(signature_version=UNSIGNED)

    return session.client(**{k: v for k, v in client_kwargs.items() if v is not None})


def _build_key(filename, folder):
    prefix = getattr(settings, 'S3_UPLOAD_PREFIX', '').strip('/')
    folder = folder.strip('/') if folder else ''
    base, ext = os.path.splitext(filename or '')
    safe_name = base or uuid4().hex
    unique_name = f"{safe_name}-{uuid4().hex}{ext or ''}"
    parts = [p for p in [prefix, folder, unique_name] if p]
    return '/'.join(parts)


def _public_url_for_key(key):
    quoted_key = quote(key.lstrip('/'), safe='/')
    base_url = getattr(settings, 'S3_UPLOAD_PUBLIC_BASE_URL', '') or getattr(settings, 'PUBLIC_MEDIA_BASE_URL', '')
    if base_url:
        return f"{base_url.rstrip('/')}/{quoted_key}"

    endpoint = getattr(settings, 'S3_UPLOAD_ENDPOINT', '')
    bucket = getattr(settings, 'S3_UPLOAD_BUCKET', '')
    region = getattr(settings, 'S3_UPLOAD_REGION', '')

    if endpoint:
        return f"{endpoint.rstrip('/')}/{bucket}/{quoted_key}"
    if region:
        return f"https://{bucket}.s3.{region}.amazonaws.com/{quoted_key}"
    return quoted_key


def upload_fileobj(file_obj, *, folder='inventory', acl='public-read'):
    client = _client()
    bucket = getattr(settings, 'S3_UPLOAD_BUCKET')
    key = _build_key(file_obj.name, folder)
    content_type = getattr(file_obj, 'content_type', None) or mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'

    file_obj.seek(0)
    extra_args = {'ACL': acl, 'ContentType': content_type}
    client.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra_args)

    return key, _public_url_for_key(key)
