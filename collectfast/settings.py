from typing import Container
from typing import Type
from typing import TypeVar

from django.conf import settings
from typing_extensions import Final


T = TypeVar("T")


def _get_setting(type_: Type[T], key: str, default: T) -> T:
    value = getattr(settings, key, default)
    if not isinstance(value, type_):
        raise ValueError(
            f"The {key!r} setting must be of type {type_!r}, found {type(value)}"
        )
    return value


debug: Final = _get_setting(
    bool, "COLLECTFAST_DEBUG", _get_setting(bool, "DEBUG", False)
)
cache_key_prefix: Final = _get_setting(
    str, "COLLECTFAST_CACHE_KEY_PREFIX", "collectfast06_asset_"
)
cache: Final = _get_setting(str, "COLLECTFAST_CACHE", "default")
threads: Final = _get_setting(int, "COLLECTFAST_THREADS", 0)
enabled: Final = _get_setting(bool, "COLLECTFAST_ENABLED", True)
aws_is_gzipped: Final = _get_setting(bool, "AWS_IS_GZIPPED", False)
gzip_content_types: Final[Container] = _get_setting(
    tuple,
    "GZIP_CONTENT_TYPES",
    (
        "text/css",
        "text/javascript",
        "application/javascript",
        "application/x-javascript",
        "image/svg+xml",
    ),
)
