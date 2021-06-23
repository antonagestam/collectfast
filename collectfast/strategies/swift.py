import logging
from typing import Optional

from swift.storage import StaticSwiftStorage

from .base import CachingHashStrategy
from collectfast import settings

logger = logging.getLogger(__name__)


class OpenStackSwiftStrategy(CachingHashStrategy[StaticSwiftStorage]):
    def __init__(self, remote_storage: StaticSwiftStorage) -> None:
        super().__init__(remote_storage)
        self.remote_hashes = {}
        # gzip support is available on github but not in the pypi release.
        if getattr(remote_storage, "gzip_content_types", []):
            self.use_gzip = True
            settings.gzip_compresslevel = remote_storage.gzip_compression_level
            settings.gzip_content_types = remote_storage.gzip_content_types
            if (
                remote_storage.gzip_unknown_content_type
                and "application/octet-stream" not in settings.gzip_content_types
            ):
                settings.gzip_content_types.append("application/octet-stream")

    def pre_collect_hook(self) -> None:
        # Collect the object listing with hashes once and share it with all threads.
        self.remote_hashes = dict(
            (obj["name"], obj["hash"])
            for obj in self.remote_storage.swift_conn.get_container(
                self.remote_storage.container_name, full_listing=True
            )[1]
        )

    def get_remote_file_hash(self, prefixed_path: str) -> Optional[str]:
        return self.remote_hashes.get(prefixed_path)

    def pre_should_copy_hook(self) -> None:
        if settings.threads:
            logger.info("Resetting connection")
            self.remote_storage._swift_conn = None
