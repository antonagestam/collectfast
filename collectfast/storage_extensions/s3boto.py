from storages.utils import safe_join

from collectfast.storage_extensions.base import BaseStorageExtensions, check_preload_metadata


class S3BotoStorageExtensions(BaseStorageExtensions):
    """
    Storage extensions for django-storage's `S3BotoStorage`
    """

    def __init__(self, storage):
        super(S3BotoStorageExtensions, self).__init__(storage)
        check_preload_metadata(storage)

    def reset_connection(self):
        pass

    def get_remote_etag(self, prefixed_path):
        normalized_path = safe_join(self.storage.location, prefixed_path).replace('\\', '/')
        try:
            return self.storage.bucket.get_key(normalized_path).etag
        except AttributeError:
            return None
