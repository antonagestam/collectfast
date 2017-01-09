from django.conf import settings

debug = getattr(
    settings, "COLLECTFAST_DEBUG", getattr(settings, "DEBUG", False))
cache_key_prefix = getattr(
    settings, "COLLECTFAST_CACHE_KEY_PREFIX", "collectfast05_asset_")
cache = getattr(settings, "COLLECTFAST_CACHE", "default")
threads = getattr(settings, "COLLECTFAST_THREADS", False)
enabled = getattr(settings, "COLLECTFAST_ENABLED", True)
preload_metadata_enabled = True is getattr(
    settings, 'AWS_PRELOAD_METADATA', False)
