from importlib import reload

import pytest
from django.test.utils import override_settings

from collectfast import settings


@override_settings(FOO=2)
def test_get_setting_returns_valid_value():
    assert 2 == settings._get_setting(int, "FOO", 1)


def test_get_setting_returns_default_value_for_missing_setting():
    assert 1 == settings._get_setting(int, "FOO", 1)


@override_settings(FOO="bar")
def test_get_setting_raises_for_invalid_type():
    with pytest.raises(ValueError):
        settings._get_setting(int, "FOO", 1)


def test_basic_settings():
    with override_settings(
        COLLECTFAST_DEBUG=True,
        COLLECTFAST_CACHE="custom",
        COLLECTFAST_ENABLED=False,
        AWS_IS_GZIPPED=True,
        GZIP_CONTENT_TYPES=("text/css", "text/javascript"),
        COLLECTFAST_THREADS=0,
    ):
        reload(settings)
        assert settings.debug is True
        assert isinstance(settings.cache_key_prefix, str)
        assert settings.cache == "custom"
        assert settings.enabled is False
        assert isinstance(settings.gzip_content_types, tuple)
        assert settings.threads == 0


def test_settings_with_threads():
    with override_settings(COLLECTFAST_THREADS=22):
        reload(settings)
        assert settings.threads == 22


@pytest.mark.parametrize(
    "django_settings",
    (
        {"COLLECTFAST_DEBUG": "True"},
        {"COLLECTFAST_CACHE_KEY_PREFIX": 1},
        {"COLLECTFAST_CACHE": None},
        {"COLLECTFAST_THREADS": None},
        {"COLLECTFAST_ENABLED": 1},
        {"AWS_IS_GZIPPED": "yes"},
        {"GZIP_CONTENT_TYPES": "not tuple"},
    ),
)
def test_invalid_setting_type_raises_value_error(django_settings):
    with override_settings(**django_settings):
        with pytest.raises(ValueError):
            reload(settings)
