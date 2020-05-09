from functools import lru_cache
from typing import Optional

from django.core.files.storage import FileSystemStorage
from django.core.files.storage import Storage

from .base import cache
from .base import CachingHashStrategy
from .base import HashStrategy


class FileSystemStrategy(HashStrategy[FileSystemStorage]):
    def get_remote_file_hash(self, prefixed_path: str) -> Optional[str]:
        try:
            return self.get_local_file_hash(prefixed_path, self.remote_storage)
        except FileNotFoundError:
            return None


class CachingFileSystemStrategy(
        CachingHashStrategy[FileSystemStorage],
        FileSystemStrategy,
):
    @lru_cache()
    def get_local_file_hash(self, *args, **kwargs):
        '''
        caches the local file hash in memory so the hash is only computed once
        per run and `post_copy_hook` method the does not duplicate work
        '''
        return super().get_local_file_hash(*args, **kwargs)
    
    def post_copy_hook(
            self, path: str, prefixed_path: str, local_storage: Storage
    ) -> None:
        cache_key = self.get_cache_key(path)
        hash_ = self.get_local_file_hash(path, local_storage)
        cache.set(cache_key, hash_)
