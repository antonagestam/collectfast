import hashlib
import logging
from functools import lru_cache
from typing import Any
from typing import Callable
from typing import Optional

import botocore.exceptions
from django.core.files.storage import Storage
from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import safe_join

from .base import CachingHashStrategy
from collectfast import settings

logger = logging.getLogger(__name__)


class Boto3Strategy(CachingHashStrategy[S3Boto3Storage]):
    def __init__(self, remote_storage: S3Boto3Storage) -> None:
        super().__init__(remote_storage)
        self.remote_storage.preload_metadata = True
        self.use_gzip = settings.aws_is_gzipped

    def _normalize_path(self, prefixed_path: str) -> str:
        path = str(safe_join(self.remote_storage.location, prefixed_path))
        return path.replace("\\", "")

    @staticmethod
    def _clean_hash(quoted_hash: Optional[str]) -> Optional[str]:
        """boto returns hashes wrapped in quotes that need to be stripped."""
        if quoted_hash is None:
            return None
        assert quoted_hash[0] == quoted_hash[-1] == '"'
        return quoted_hash[1:-1]

    def get_local_multipart_hash(
        self, path: str, local_storage: Storage, chunk_size: int
    ) -> str:
        """Calculate multipart hash using a given chunk size."""
        md5s = []
        with local_storage.open(path, "rb") as f:
            func: Callable[[], Any] = lambda: f.read(chunk_size)
            for data in iter(func, b""):
                md5s.append(hashlib.md5(data).digest())
        m = hashlib.md5(b"".join(md5s))
        return "{}-{}".format(m.hexdigest(), len(md5s))

    @lru_cache(maxsize=None)
    def get_local_file_hash(
        self, path: str, local_storage: Storage, chunk_size: int = 8 * 1024 * 1024
    ) -> str:
        """Calculate large file hashes differently."""
        file = local_storage.open(path)
        if file.size > chunk_size:
            return self.get_local_multipart_hash(path, local_storage, chunk_size)
        return super().get_local_file_hash(path, local_storage)

    def get_remote_file_hash(self, prefixed_path: str) -> Optional[str]:
        normalized_path = self._normalize_path(prefixed_path)
        logger.debug("Getting file hash", extra={"normalized_path": normalized_path})
        try:
            hash_: str = self.remote_storage.bucket.Object(normalized_path).e_tag
        except botocore.exceptions.ClientError:
            logger.debug("Error on remote hash request", exc_info=True)
            return None
        return self._clean_hash(hash_)

    def pre_should_copy_hook(self) -> None:
        if settings.threads:
            logger.info("Resetting connection")
            self.remote_storage._connection = None
