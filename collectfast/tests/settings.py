import os
import pathlib

base_path = pathlib.Path.cwd()

# Set USE_TZ to True to work around bug in django-storages
USE_TZ = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-collectfast",
    }
}
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
    "django.template.loaders.eggs.Loader",
)
TEMPLATE_DIRS = [str(base_path / "collectfast/templates")]
INSTALLED_APPS = ("collectfast", "django.contrib.staticfiles")
STATIC_URL = "/staticfiles/"
STATIC_ROOT = str(base_path / "static_root")
STATICFILES_DIRS = [str(base_path / "static")]
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
COLLECTFAST_STRATEGY = "collectfast.strategies.boto3.Boto3Strategy"
COLLECTFAST_DEBUG = True
AWS_PRELOAD_METADATA = True
AWS_STORAGE_BUCKET_NAME = "collectfast"
AWS_IS_GZIPPED = False
GZIP_CONTENT_TYPES = ("text/plain",)
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
AWS_S3_REGION_NAME = "eu-central-1"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = None
S3_USE_SIGV4 = True
AWS_S3_HOST = "s3.eu-central-1.amazonaws.com"
SECRET_KEY = "nonsense"
