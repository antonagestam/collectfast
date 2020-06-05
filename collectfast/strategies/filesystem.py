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
    CachingHashStrategy[FileSystemStorage], FileSystemStrategy,
):
    ...
