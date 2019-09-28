from typing import Sequence

from django.conf import settings
from typing_extensions import Final


debug = getattr(
    settings, "COLLECTFAST_DEBUG", getattr(settings, "DEBUG", False)
)  # type: Final[bool]
cache_key_prefix = getattr(
    settings, "COLLECTFAST_CACHE_KEY_PREFIX", "collectfast06_asset_"
)  # type: Final[str]
cache = getattr(settings, "COLLECTFAST_CACHE", "default")  # type: Final[str]
threads = getattr(settings, "COLLECTFAST_THREADS", False)  # type: Final[bool]
enabled = getattr(settings, "COLLECTFAST_ENABLED", True)  # type: Final[bool]
aws_is_gzipped = getattr(settings, "AWS_IS_GZIPPED", False)  # type: Final[bool]
gzip_content_types = getattr(
    settings,
    "GZIP_CONTENT_TYPES",
    (
        "text/css",
        "text/javascript",
        "application/javascript",
        "application/x-javascript",
        "image/svg+xml",
    ),
)  # type: Final[Sequence[str]]
