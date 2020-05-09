from typing import Optional

from django.core.files.storage import FileSystemStorage

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
    def post_copy_hook(
            self, path: str, prefixed_path: str, local_storage: Storage, copied: bool
    ) -> None:
        if copied:
            cache_key = self.get_cache_key(path)
            hash_ = self.get_local_file_hash(path, local_storage)
            cache.set(cache_key, hash_)
