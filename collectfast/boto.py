from . import settings

try:
    from storages.backends.s3boto import S3BotoStorage
    from storages.backends.s3boto3 import S3Boto3Storage
    has_boto = True
except:
    has_boto = False


def is_boto3(storage):
    return has_boto and isinstance(storage, S3Boto3Storage)


def is_boto(storage):
    return has_boto and (
        isinstance(storage, S3BotoStorage) or
        isinstance(storage, S3Boto3Storage))


def reset_connection(storage):
    """
    Reset connection if thread pooling is enabled and storage is boto3.
    """
    if settings.threads and is_boto3(storage):
        storage._connection = None
