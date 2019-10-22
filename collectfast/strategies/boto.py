import logging
import warnings
from typing import Optional

import boto.exception
from storages.backends.s3boto import S3BotoStorage
from storages.utils import safe_join

from .base import CachingHashStrategy
from collectfast import settings

logger = logging.getLogger(__name__)


class BotoStrategy(CachingHashStrategy[S3BotoStorage]):
    def __init__(self, remote_storage):
        # type: (S3BotoStorage) -> None
        warnings.warn(
            "The BotoStrategy class is deprecated and will be removed in Collectfast "
            "2.0.",
            DeprecationWarning,
        )
        super().__init__(remote_storage)
        self.remote_storage.preload_metadata = True
        self.use_gzip = settings.aws_is_gzipped

    def _normalize_path(self, prefixed_path):
        # type: (str) -> str
        full_path = str(safe_join(self.remote_storage.location, prefixed_path))
        return full_path.replace("\\", "/")

    @staticmethod
    def _clean_hash(quoted_hash):
        # type: (Optional[str]) -> Optional[str]
        """boto returns hashes wrapped in quotes that need to be stripped."""
        if quoted_hash is None:
            return None
        assert quoted_hash[0] == quoted_hash[-1] == '"'
        return quoted_hash[1:-1]

    def get_remote_file_hash(self, prefixed_path):
        # type: (str) -> Optional[str]
        normalized_path = self._normalize_path(prefixed_path)
        logger.debug("Getting file hash", extra={"normalized_path": normalized_path})
        try:
            hash_ = self.remote_storage.bucket.get_key(
                normalized_path
            ).etag  # type: str
        except AttributeError:
            return None
        except boto.exception.S3ResponseError:
            logger.debug("Error on remote hash request", exc_info=True)
            return None
        return self._clean_hash(hash_)
