import base64
import binascii
from typing import Optional

from google.api_core.exceptions import NotFound
from storages.backends.gcloud import GoogleCloudStorage

from .base import CachingHashStrategy


class GoogleCloudStrategy(CachingHashStrategy[GoogleCloudStorage]):
    delete_not_found_exception = (NotFound,)

    def get_remote_file_hash(self, prefixed_path: str) -> Optional[str]:
        normalized_path = prefixed_path.replace("\\", "/")
        blob = self.remote_storage.bucket.get_blob(normalized_path)
        if blob is None:
            return blob
        md5_base64 = blob._properties["md5Hash"]
        return binascii.hexlify(base64.urlsafe_b64decode(md5_base64)).decode()
