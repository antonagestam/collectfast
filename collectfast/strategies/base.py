import abc
import gzip
import hashlib
import logging
import mimetypes
import pydoc
from functools import lru_cache
from io import BytesIO
from typing import ClassVar
from typing import Generic
from typing import NoReturn
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union

from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.encoding import force_bytes

from collectfast import settings


_RemoteStorage = TypeVar("_RemoteStorage", bound=Storage)


cache = caches[settings.cache]
logger = logging.getLogger(__name__)


class Strategy(abc.ABC, Generic[_RemoteStorage]):
    # Exceptions raised by storage backend for delete calls to non-existing
    # objects. The command silently catches these.
    delete_not_found_exception: ClassVar[Tuple[Type[Exception], ...]] = ()

    def __init__(self, remote_storage: _RemoteStorage) -> None:
        self.remote_storage = remote_storage

    @abc.abstractmethod
    def should_copy_file(
        self, path: str, prefixed_path: str, local_storage: Storage
    ) -> bool:
        """
        Called for each file before copying happens, this method decides
        whether a file should be copied or not. Return False to indicate that
        the file is already up-to-date and should not be copied, or True to
        indicate that it is stale and needs updating.
        """
        ...

    def pre_should_copy_hook(self) -> None:
        """Hook called before calling should_copy_file."""
        ...

    def post_copy_hook(
        self, path: str, prefixed_path: str, local_storage: Storage
    ) -> None:
        """Hook called after a file is copied."""
        ...

    def on_skip_hook(
        self, path: str, prefixed_path: str, local_storage: Storage
    ) -> None:
        """Hook called when a file copy is skipped."""
        ...


class HashStrategy(Strategy[_RemoteStorage], abc.ABC):
    use_gzip = False

    def should_copy_file(
        self, path: str, prefixed_path: str, local_storage: Storage
    ) -> bool:
        local_hash = self.get_local_file_hash(path, local_storage)
        remote_hash = self.get_remote_file_hash(prefixed_path)
        return local_hash != remote_hash

    def get_gzipped_local_file_hash(
        self, uncompressed_file_hash: str, path: str, contents: str
    ) -> str:
        buffer = BytesIO()
        zf = gzip.GzipFile(mode="wb", fileobj=buffer, mtime=0.0)
        zf.write(force_bytes(contents))
        zf.close()
        return hashlib.md5(buffer.getvalue()).hexdigest()

    @lru_cache(maxsize=None)
    def get_local_file_hash(self, path: str, local_storage: Storage) -> str:
        """Create md5 hash from file contents."""
        # Read file contents and handle file closing
        file = local_storage.open(path)
        try:
            contents = file.read()
        finally:
            file.close()

        file_hash = hashlib.md5(contents).hexdigest()

        # Check if content should be gzipped and hash gzipped content
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if self.use_gzip and content_type in settings.gzip_content_types:
            file_hash = self.get_gzipped_local_file_hash(file_hash, path, contents)

        return file_hash

    @abc.abstractmethod
    def get_remote_file_hash(self, prefixed_path: str) -> Optional[str]:
        ...


class CachingHashStrategy(HashStrategy[_RemoteStorage], abc.ABC):
    @lru_cache(maxsize=None)
    def get_cache_key(self, path: str) -> str:
        path_hash = hashlib.md5(path.encode()).hexdigest()
        return settings.cache_key_prefix + path_hash

    def invalidate_cached_hash(self, path: str) -> None:
        cache.delete(self.get_cache_key(path))

    def should_copy_file(
        self, path: str, prefixed_path: str, local_storage: Storage
    ) -> bool:
        local_hash = self.get_local_file_hash(path, local_storage)
        remote_hash = self.get_cached_remote_file_hash(path, prefixed_path)
        if local_hash != remote_hash:
            # invalidate cached hash, since we expect its corresponding file to
            # be overwritten
            self.invalidate_cached_hash(path)
            return True
        return False

    def get_cached_remote_file_hash(self, path: str, prefixed_path: str) -> str:
        """Cache the hash of the remote storage file."""
        cache_key = self.get_cache_key(path)
        hash_ = cache.get(cache_key, False)
        if hash_ is False:
            hash_ = self.get_remote_file_hash(prefixed_path)
            cache.set(cache_key, hash_)
        return str(hash_)

    def get_gzipped_local_file_hash(
        self, uncompressed_file_hash: str, path: str, contents: str
    ) -> str:
        """Cache the hash of the gzipped local file."""
        cache_key = self.get_cache_key("gzip_hash_%s" % uncompressed_file_hash)
        file_hash = cache.get(cache_key, False)
        if file_hash is False:
            file_hash = super().get_gzipped_local_file_hash(
                uncompressed_file_hash, path, contents
            )
            cache.set(cache_key, file_hash)
        return str(file_hash)

    def post_copy_hook(
        self, path: str, prefixed_path: str, local_storage: Storage
    ) -> None:
        """Cache the hash of the just copied local file."""
        super().post_copy_hook(path, prefixed_path, local_storage)
        key = self.get_cache_key(path)
        value = self.get_local_file_hash(path, local_storage)
        cache.set(key, value)


class DisabledStrategy(Strategy):
    def should_copy_file(
        self, path: str, prefixed_path: str, local_storage: Storage
    ) -> NoReturn:
        raise NotImplementedError

    def pre_should_copy_hook(self) -> NoReturn:
        raise NotImplementedError


def load_strategy(klass: Union[str, type, object]) -> Type[Strategy[Storage]]:
    if isinstance(klass, str):
        klass = pydoc.locate(klass)
    if not isinstance(klass, type) or not issubclass(klass, Strategy):
        raise ImproperlyConfigured(
            "Configured strategies must be subclasses of %s.%s"
            % (Strategy.__module__, Strategy.__qualname__)
        )
    return klass
