from storages.utils import safe_join

from collectfast import settings
from collectfast.storage_extensions.base import BaseStorageExtensions, check_preload_metadata


class S3Boto3StorageExtensions(BaseStorageExtensions):
    """
    Storage extensions for django-storage's `S3Boto3Storage`
    """

    def __init__(self, storage):
        super(S3Boto3StorageExtensions, self).__init__(storage)
        check_preload_metadata(storage)

    def reset_connection(self):
        """
        Reset connection if thread pooling is enabled
        """
        if settings.threads:
            self.storage._connection = None

    def get_etag(self, path):
        normalized_path = safe_join(self.storage.location, path).replace('\\', '/')
        try:
            return self.storage.bucket.Object(normalized_path).e_tag
        except:
            pass
