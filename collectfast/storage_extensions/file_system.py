import gzip
import hashlib
import logging
import mimetypes

from django.core.cache import caches
from django.utils.encoding import force_bytes
from django.utils.six import BytesIO

from collectfast import settings
from collectfast.etag import get_cache_key
from collectfast.storage_extensions.base import BaseStorageExtensions

cache = caches[settings.cache]
logger = logging.getLogger(__name__)


class FileSystemStorageExtensions(BaseStorageExtensions):
    """
    Storage extensions for `Storage` classes `FileSystemStorage` or anything using the local file system
    """

    def get_etag(self, path):
        contents = self.storage.open(path).read()
        file_hash = hashlib.md5(contents).hexdigest()

        # Check if content should be gzipped and hash gzipped content
        content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        if settings.is_gzipped and content_type in settings.gzip_content_types:
            cache_key = get_cache_key('gzip_hash_%s' % file_hash)
            file_hash = cache.get(cache_key, False)
            if file_hash is False:
                buffer = BytesIO()
                zf = gzip.GzipFile(
                    mode='wb', compresslevel=6, fileobj=buffer, mtime=0.0)
                zf.write(force_bytes(contents))
                zf.close()
                file_hash = hashlib.md5(buffer.getvalue()).hexdigest()
                cache.set(cache_key, file_hash)

        return '"%s"' % file_hash
