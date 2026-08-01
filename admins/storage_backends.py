from django.conf import settings
from django.core.files.storage import FileSystemStorage


def get_resource_storage():
    """Storage for Digital Resource uploads. Uses Wasabi (S3-compatible) when
    credentials are configured; falls back to local disk otherwise (e.g. dev
    without Wasabi set up yet). Called lazily so importing this module never
    requires the credentials to be present.
    """
    if getattr(settings, 'WASABI_ACCESS_KEY', '') and getattr(settings, 'WASABI_SECRET_KEY', ''):
        from storages.backends.s3boto3 import S3Boto3Storage
        return S3Boto3Storage(
            access_key=settings.WASABI_ACCESS_KEY,
            secret_key=settings.WASABI_SECRET_KEY,
            bucket_name=settings.WASABI_BUCKET_NAME,
            endpoint_url=settings.WASABI_ENDPOINT_URL,
            region_name=settings.WASABI_REGION,
            file_overwrite=False,
            default_acl=None,
            querystring_auth=True,
        )
    return FileSystemStorage()
