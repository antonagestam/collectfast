import gzip
import hashlib
import logging
import mimetypes
from functools import lru_cache
from io import BytesIO
from typing import Final
from typing import IO
from typing import Optional

import botocore.exceptions
from django.core.cache import caches
from django.core.files.storage import Storage
from django.utils.encoding import force_bytes
from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import safe_join

from .base import CachingHashStrategy
from collectfast import settings


cache = caches[settings.cache]
logger = logging.getLogger(__name__)

multipart_chunksize: Final = 8 * 1024 * 1024
# AWS changes the way hashes are calculated when using multipart uploads,
# which are enabled by default when file size exceeds 8388608 bytes.
# Django-storages does not currently allow a user to override this default.
# See also:
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Object.upload_fileobj
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/s3.html#boto3.s3.transfer.TransferConfig


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

    def get_aws_hash(self, open_handle: IO) -> str:
        """Calculate multipart-friendly hash using `multipart_chunksize` chunk size."""
        chunk_hashes = []
        while True:
            data = open_handle.read(multipart_chunksize)
            if not data:
                break
            chunk_hashes.append(hashlib.md5(data))

        if len(chunk_hashes) < 1:
            return "{}".format(hashlib.md5().hexdigest())

        if len(chunk_hashes) == 1:
            return "{}".format(chunk_hashes[0].hexdigest())

        digests = b"".join(m.digest() for m in chunk_hashes)
        digests_md5 = hashlib.md5(digests)
        return "{}-{}".format(digests_md5.hexdigest(), len(chunk_hashes))

    def get_gzipped_aws_hash(self, open_handle: IO) -> str:
        """Calculate multipart-friendly gzipped hash."""
        buffer = BytesIO()
        zf = gzip.GzipFile(mode="wb", fileobj=buffer, mtime=0.0)
        zf.write(force_bytes(open_handle.read()))
        zf.close()
        buffer.seek(0)
        return self.get_aws_hash(buffer)

    @lru_cache(maxsize=None)
    def get_local_file_hash(self, path: str, local_storage: Storage) -> str:
        """Calculate large file hashes differently, if necessary."""
        # # Check if content should be gzipped and hash gzipped content
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with local_storage.open(path, "rb") as f:
            file_hash = self.get_aws_hash(f)
            if self.use_gzip and content_type in settings.gzip_content_types:
                cache_key = self.get_cache_key("gzip_hash_%s" % file_hash)
                file_hash = cache.get(cache_key, False)
                if file_hash is False:
                    f.seek(0)
                    file_hash = self.get_gzipped_aws_hash(f)
                    cache.set(cache_key, file_hash)

        return str(file_hash)

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
