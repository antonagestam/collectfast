from typing import Any

from . import settings

has_boto = True  # type: bool
has_boto3 = True  # type: bool

try:
    from storages.backends.s3boto import S3BotoStorage
except ImportError:
    has_boto = False

try:
    from storages.backends.s3boto3 import S3Boto3Storage
except ImportError:
    has_boto3 = False


def is_boto3(storage):
    # type: (Any) -> bool
    return has_boto3 and isinstance(storage, S3Boto3Storage)


def is_boto(storage):
    # type: (Any) -> bool
    return has_boto and (
        isinstance(storage, S3BotoStorage) or isinstance(storage, S3Boto3Storage)
    )


def reset_connection(storage):
    # type: (Any) -> None
    """
    Reset connection if thread pooling is enabled and storage is boto3.
    """
    if settings.threads and is_boto3(storage):
        storage._connection = None
