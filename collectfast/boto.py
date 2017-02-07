from . import settings


def is_boto3(storage):
    return type(storage).__name__ == 'S3Boto3Storage'


def reset_connection(storage):
    """
    Reset connection if thread pooling is enabled and storage is boto3.
    """
    if settings.threads and is_boto3(storage):
        storage._connection = None
