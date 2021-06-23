import os
import pathlib
import tempfile

from google.oauth2 import service_account

env = os.environ.get

base_path = pathlib.Path.cwd()

# Set USE_TZ to True to work around bug in django-storages
USE_TZ = True

SECRET_KEY = "nonsense"
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
MEDIA_ROOT = str(base_path / "fs_remote")
STATICFILES_DIRS = [str(base_path / "static")]
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
COLLECTFAST_STRATEGY = "collectfast.strategies.boto3.Boto3Strategy"
COLLECTFAST_DEBUG = True
COLLECTFAST_GZIP_COMPRESSLEVEL = 9

GZIP_CONTENT_TYPES = ("text/plain",)

# AWS
AWS_PRELOAD_METADATA = True
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", "collectfast")
AWS_IS_GZIPPED = False
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")
AWS_S3_SIGNATURE_VERSION = env("AWS_S3_SIGNATURE_VERSION", "s3v4")
AWS_QUERYSTRING_AUTH = False  # This is also enforced by S3StaticStorage
AWS_DEFAULT_ACL = None
S3_USE_SIGV4 = True


# Google Cloud
gcloud_credentials_json = env("GCLOUD_CREDENTIALS")
if not gcloud_credentials_json:
    GS_CREDENTIALS = None
else:
    with tempfile.NamedTemporaryFile() as file:
        file.write(gcloud_credentials_json.encode())
        file.read()
        GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
            file.name
        )
GS_BUCKET_NAME = env("GS_BUCKET_NAME", "roasted-dufus")

# OpenStack Swift
SWIFT_AUTH_URL = env("SWIFT_AUTH_URL")
SWIFT_PROJECT_ID = env("SWIFT_PROJECT_ID")
SWIFT_PROJECT_NAME = env("SWIFT_PROJECT_NAME")
SWIFT_USER_DOMAIN_NAME = env("SWIFT_USER_DOMAIN_NAME")
SWIFT_PROJECT_DOMAIN_ID = env("SWIFT_PROJECT_DOMAIN_ID")
SWIFT_USERNAME = env("SWIFT_USERNAME")
SWIFT_PASSWORD = env("SWIFT_PASSWORD")
SWIFT_REGION_NAME = env("SWIFT_REGION_NAME")
SWIFT_STATIC_CONTAINER_NAME = env("SWIFT_STATIC_CONTAINER_NAME")
