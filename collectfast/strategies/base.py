import abc
import gzip
import hashlib
import logging
import mimetypes
import warnings
from functools import lru_cache
from io import BytesIO
from pydoc import locate
from typing import Generic
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.encoding import force_bytes
from typing_extensions import Final

from collectfast import settings


_RemoteStorage = TypeVar("_RemoteStorage", bound=Storage)


cache = caches[settings.cache]
logger = logging.getLogger(__name__)


class Strategy(abc.ABC, Generic[_RemoteStorage]):
    def __init__(self, remote_storage):
        # type: (_RemoteStorage) -> None
        self.remote_storage = remote_storage

    @abc.abstractmethod
    def should_copy_file(self, path, prefixed_path, local_storage):
        # type: (str, str, Storage) -> bool
        """
        Called for each file before copying happens, this method decides
        whether a file should be copied or not. Return False to indicate that
        the file is already up-to-date and should not be copied, or True to
        indicate that it is stale and needs updating.
        """
        ...

    def pre_should_copy_hook(self):
        # type: () -> None
        """Hook called before calling should_copy_file."""
        ...


class HashStrategy(Strategy[_RemoteStorage], abc.ABC):
    use_gzip = False

    def should_copy_file(self, path, prefixed_path, local_storage):
        # type: (str, str, Storage) -> bool
        local_hash = self.get_local_file_hash(path, local_storage)
        remote_hash = self.get_remote_file_hash(prefixed_path)
        return local_hash != remote_hash

    def get_gzipped_local_file_hash(self, uncompressed_file_hash, path, contents):
        # type: (str, str, str) -> str
        buffer = BytesIO()
        zf = gzip.GzipFile(mode="wb", compresslevel=6, fileobj=buffer, mtime=0.0)
        zf.write(force_bytes(contents))
        zf.close()
        return hashlib.md5(buffer.getvalue()).hexdigest()

    def get_local_file_hash(self, path, local_storage):
        # type: (str, Storage) -> str
        """Create md5 hash from file contents."""
        contents = local_storage.open(path).read()
        file_hash = hashlib.md5(contents).hexdigest()

        # Check if content should be gzipped and hash gzipped content
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if self.use_gzip and content_type in settings.gzip_content_types:
            file_hash = self.get_gzipped_local_file_hash(file_hash, path, contents)

        return file_hash

    @abc.abstractmethod
    def get_remote_file_hash(self, prefixed_path):
        # type: (str) -> Optional[str]
        ...


class CachingHashStrategy(HashStrategy[_RemoteStorage], abc.ABC):
    @lru_cache()
    def get_cache_key(self, path):
        # type: (str) -> str
        path_hash = hashlib.md5(path.encode()).hexdigest()
        return settings.cache_key_prefix + path_hash

    def invalidate_cached_hash(self, path):
        # type: (str) -> None
        cache.delete(self.get_cache_key(path))

    def should_copy_file(self, path, prefixed_path, local_storage):
        # type: (str, str, Storage) -> bool
        local_hash = self.get_local_file_hash(path, local_storage)
        remote_hash = self.get_cached_remote_file_hash(path, prefixed_path)
        if local_hash != remote_hash:
            # invalidate cached hash, since we expect its corresponding file to
            # be overwritten
            self.invalidate_cached_hash(path)
            return True
        return False

    def get_cached_remote_file_hash(self, path, prefixed_path):
        # type: (str, str) -> str
        """Cache the hash of the remote storage file."""
        cache_key = self.get_cache_key(path)
        hash_ = cache.get(cache_key, False)
        if hash_ is False:
            hash_ = self.get_remote_file_hash(prefixed_path)
            cache.set(cache_key, hash_)
        return str(hash_)

    def get_gzipped_local_file_hash(self, uncompressed_file_hash, path, contents):
        # type: (str, str, str) -> str
        """Cache the hash of the gzipped local file."""
        cache_key = self.get_cache_key("gzip_hash_%s" % uncompressed_file_hash)
        file_hash = cache.get(cache_key, False)
        if file_hash is False:
            file_hash = super().get_gzipped_local_file_hash(
                uncompressed_file_hash, path, contents
            )
            cache.set(cache_key, file_hash)
        return str(file_hash)


def load_strategy(klass: Union[str, type, object]) -> Type[Strategy]:
    if isinstance(klass, str):
        klass = locate(klass)
    if not isinstance(klass, type) or not issubclass(klass, Strategy):
        raise ImproperlyConfigured(
            "Configured strategies must be subclasses of %s.%s"
            % (Strategy.__module__, Strategy.__qualname__)
        )
    return klass


_BOTO_STORAGE = "storages.backends.s3boto.S3BotoStorage"  # type: Final
_BOTO_STRATEGY = "collectfast.strategies.boto.BotoStrategy"  # type: Final
_BOTO3_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"  # type: Final
_BOTO3_STRATEGY = "collectfast.strategies.boto3.Boto3Strategy"  # type: Final


def _resolves_to_subclass(subclass_ref: str, superclass_ref: str) -> bool:
    subclass = locate(subclass_ref)
    assert isinstance(subclass, type)
    try:
        superclass = locate(superclass_ref)
        assert isinstance(superclass, type)
    except (ImportError, AssertionError) as e:
        logger.debug("Failed to import %s: %s" % (superclass_ref, e))
        return False
    return issubclass(subclass, superclass)


def guess_strategy(storage: str) -> str:
    warnings.warn(
        "Falling back to guessing strategy for backwards compatibility. This "
        "is deprecated and will be removed in a future release. Explicitly "
        "set COLLECTFAST_STRATEGY to silence this warning."
    )
    if storage == _BOTO_STORAGE:
        return _BOTO_STRATEGY
    if storage == _BOTO3_STORAGE:
        return _BOTO3_STRATEGY
    if _resolves_to_subclass(storage, _BOTO_STORAGE):
        return _BOTO_STRATEGY
    if _resolves_to_subclass(storage, _BOTO3_STORAGE):
        return _BOTO3_STRATEGY
    raise ImproperlyConfigured(
        "No strategy configured, please make sure COLLECTFAST_STRATEGY is set."
    )
