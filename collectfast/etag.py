import hashlib
import logging

from django.core.cache import caches

from collectfast import settings
from collectfast.storage_extensions import get_storage_extensions

try:
    from functools import lru_cache
except ImportError:
    # make lru_cache do nothing in python 2.7
    def lru_cache(maxsize=128, typed=False):
        def decorator(func):
            return func
        return decorator

cache = caches[settings.cache]
logger = logging.getLogger(__name__)


@lru_cache()
def get_cache_key(path):
    """
    Create a cache key by concatenating the prefix with a hash of the path.
    """
    # Python 2/3 support for path hashing
    try:
        path_hash = hashlib.md5(path).hexdigest()
    except TypeError:
        path_hash = hashlib.md5(path.encode('utf-8')).hexdigest()
    return settings.cache_key_prefix + path_hash


def get_remote_etag(storage_extensions, prefixed_path):
    """
    Get etag of path from S3 using boto, boto3 or gcloud.
    """
    return storage_extensions.get_etag(prefixed_path)


def get_etag(storage_extensions, path, prefixed_path):
    """
    Get etag of path from cache or S3 - in that order.
    """
    cache_key = get_cache_key(path)
    etag = cache.get(cache_key, False)
    if etag is False:
        etag = get_remote_etag(storage_extensions, prefixed_path)
        cache.set(cache_key, etag)
    return etag


def destroy_etag(path):
    """
    Clear etag of path from cache.
    """
    cache.delete(get_cache_key(path))


def get_file_hash(storage_extensions, path):
    """
    Create md5 hash from file contents.
    """
    return storage_extensions.get_etag(path)


def has_matching_etag(remote_storage_extensions, source_storage, path, prefixed_path):
    """
    Compare etag of path in source storage with remote.
    """
    storage_etag = get_etag(remote_storage_extensions, path, prefixed_path)
    local_etag = get_file_hash(source_storage, path)
    return storage_etag == local_etag


def should_copy_file(remote_storage_extensions, path, prefixed_path, source_storage_extensions):
    """
    Returns True if the file should be copied, otherwise False.
    """
    if has_matching_etag(
            remote_storage_extensions, source_storage_extensions, path, prefixed_path):
        logger.info("%s: Skipping based on matching file hashes" % path)
        return False

    # Invalidate cached versions of lookup before copy
    destroy_etag(path)
    logger.info("%s: Hashes did not match" % path)
    return True
