from django.core.files.storage import Storage
from storages.backends.gcloud import GoogleCloudStorage
from storages.backends.s3boto import S3BotoStorage
from storages.backends.s3boto3 import S3Boto3Storage

from collectfast.storage_extensions import get_storage_extensions
from collectfast.storage_extensions.gcloud import GoogleCloudStorageExtensions
from collectfast.storage_extensions.s3boto import S3BotoStorageExtensions
from collectfast.storage_extensions.s3boto3 import S3Boto3StorageExtensions
from .utils import test


class UnknownStorage(Storage):
    def __init__(self):
        super(UnknownStorage, self).__init__()
    pass


class InheritedStorage(GoogleCloudStorage):
    pass


@test
def test_get_storage_extensions(case):
    case.assertIsInstance(get_storage_extensions(S3BotoStorage()), S3BotoStorageExtensions)
    case.assertIsInstance(get_storage_extensions(S3Boto3Storage()), S3Boto3StorageExtensions)
    case.assertIsInstance(get_storage_extensions(GoogleCloudStorage()), GoogleCloudStorageExtensions)
    case.assertIsInstance(get_storage_extensions(InheritedStorage()), GoogleCloudStorageExtensions)
    with case.assertRaises(RuntimeError):
        get_storage_extensions(UnknownStorage())
