from django.conf import settings

debug = getattr(
    settings, "COLLECTFAST_DEBUG", getattr(settings, "DEBUG", False))
cache_key_prefix = getattr(
    settings, "COLLECTFAST_CACHE_KEY_PREFIX", "collectfast05_asset_")
cache = getattr(settings, "COLLECTFAST_CACHE", "default")
threads = getattr(settings, "COLLECTFAST_THREADS", False)
enabled = getattr(settings, "COLLECTFAST_ENABLED", True)
is_gzipped = getattr(settings, "AWS_IS_GZIPPED", False)
gzip_content_types = getattr(
    settings, "GZIP_CONTENT_TYPES", (
        "text/css", "text/javascript", "application/javascript",
        "application/x-javascript", "image/svg+xml"))
