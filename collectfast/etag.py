import gzip
import hashlib
import logging
import mimetypes
from functools import lru_cache
from io import BytesIO
from typing import Optional

from django.core.cache import caches
from django.core.files.storage import Storage
from django.utils.encoding import force_bytes
from storages.utils import safe_join

from collectfast import settings

cache = caches[settings.cache]
logger = logging.getLogger(__name__)


@lru_cache()
def get_cache_key(path):
    # type: (str) -> str
    """
    Create a cache key by concatenating the prefix with a hash of the path.
    """
    path_hash = hashlib.md5(path.encode()).hexdigest()
    return settings.cache_key_prefix + path_hash


def get_remote_etag(storage, prefixed_path):
    # type: (Storage, str) -> Optional[str]
    """
    Get etag of path from S3 using boto or boto3.
    """
    normalized_path = safe_join(
        storage.location,  # type: ignore
        prefixed_path,
    ).replace("\\", "/")
    try:
        return storage.bucket.get_key(normalized_path).etag  # type: ignore
    except AttributeError:
        pass
    try:
        return storage.bucket.Object(normalized_path).e_tag  # type: ignore
    except:
        pass
    return None


def get_etag(storage, path, prefixed_path):
    # type: (Storage, str, str) -> str
    """
    Get etag of path from cache or S3 - in that order.
    """
    cache_key = get_cache_key(path)
    etag = cache.get(cache_key, False)
    if etag is False:
        etag = get_remote_etag(storage, prefixed_path)
        cache.set(cache_key, etag)
    return etag


def destroy_etag(path):
    # type: (str) -> None
    """
    Clear etag of path from cache.
    """
    cache.delete(get_cache_key(path))


def get_file_hash(storage, path):
    # type: (Storage, str) -> str
    """
    Create md5 hash from file contents.
    """
    contents = storage.open(path).read()
    file_hash = hashlib.md5(contents).hexdigest()

    # Check if content should be gzipped and hash gzipped content
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if settings.is_gzipped and content_type in settings.gzip_content_types:
        cache_key = get_cache_key("gzip_hash_%s" % file_hash)
        file_hash = cache.get(cache_key, False)
        if file_hash is False:
            buffer = BytesIO()
            zf = gzip.GzipFile(mode="wb", compresslevel=6, fileobj=buffer, mtime=0.0)
            zf.write(force_bytes(contents))
            zf.close()
            file_hash = hashlib.md5(buffer.getvalue()).hexdigest()
            cache.set(cache_key, file_hash)

    return '"%s"' % file_hash


def has_matching_etag(remote_storage, source_storage, path, prefixed_path):
    # type: (Storage, Storage, str, str) -> bool
    """
    Compare etag of path in source storage with remote.
    """
    storage_etag = get_etag(remote_storage, path, prefixed_path)
    local_etag = get_file_hash(source_storage, path)
    return storage_etag == local_etag


def should_copy_file(remote_storage, path, prefixed_path, source_storage):
    # type: (Storage, str, str, Storage) -> bool
    """
    Returns True if the file should be copied, otherwise False.
    """
    if has_matching_etag(remote_storage, source_storage, path, prefixed_path):
        logger.info("%s: Skipping based on matching file hashes" % path)
        return False

    # Invalidate cached versions of lookup before copy
    destroy_etag(path)
    logger.info("%s: Hashes did not match" % path)
    return True
