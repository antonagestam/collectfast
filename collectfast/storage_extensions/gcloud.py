import base64
import binascii

from collectfast.storage_extensions.base import BaseStorageExtensions


class GoogleCloudStorageExtensions(BaseStorageExtensions):
    """
    Storage extensions for django-storage's `GoogleCloudStorage`
    """

    def reset_connection(self):
        pass

    def get_remote_etag(self, prefixed_path):
        normalized_path = prefixed_path.replace('\\', '/')
        try:
            md5_base64 = self.storage.bucket.get_blob(normalized_path)._properties['md5Hash']
            return '"' + binascii.hexlify(base64.urlsafe_b64decode(md5_base64)).decode("utf-8") + '"'
        except:
            return None
