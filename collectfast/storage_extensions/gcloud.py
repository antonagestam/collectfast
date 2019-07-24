import base64
import binascii

from google.api_core.exceptions import NotFound

from collectfast.storage_extensions.base import BaseStorageExtensions


class GoogleCloudStorageExtensions(BaseStorageExtensions):
    """
    Storage extensions for django-storage's `GoogleCloudStorage`
    """

    def get_etag(self, path):
        normalized_path = path.replace('\\', '/')
        try:
            md5_base64 = self.storage.bucket.get_blob(normalized_path)._properties['md5Hash']
            return '"' + binascii.hexlify(base64.urlsafe_b64decode(md5_base64)).decode("utf-8") + '"'
        except:
            return None

    def try_delete(self, path):
        try:
            super(GoogleCloudStorageExtensions, self).try_delete(path)
        except NotFound:
            pass
