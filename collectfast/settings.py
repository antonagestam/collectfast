from typing import Sequence

from django.conf import settings
from typing_extensions import Final


debug: Final[bool] = getattr(
    settings, "COLLECTFAST_DEBUG", getattr(settings, "DEBUG", False)
)
cache_key_prefix: Final[str] = getattr(
    settings, "COLLECTFAST_CACHE_KEY_PREFIX", "collectfast06_asset_"
)
cache: Final[str] = getattr(settings, "COLLECTFAST_CACHE", "default")
threads: Final[bool] = getattr(settings, "COLLECTFAST_THREADS", False)
enabled: Final[bool] = getattr(settings, "COLLECTFAST_ENABLED", True)
aws_is_gzipped: Final[bool] = getattr(settings, "AWS_IS_GZIPPED", False)
gzip_content_types: Final[Sequence[str]] = getattr(
    settings,
    "GZIP_CONTENT_TYPES",
    (
        "text/css",
        "text/javascript",
        "application/javascript",
        "application/x-javascript",
        "image/svg+xml",
    ),
)
