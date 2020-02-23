import pytest
from django.test.utils import override_settings

from collectfast.settings import _get_setting


@override_settings(FOO=2)
def test_get_setting_returns_valid_value():
    assert 2 == _get_setting(int, "FOO", 1)


def test_get_setting_returns_default_value_for_missing_setting():
    assert 1 == _get_setting(int, "FOO", 1)


@override_settings(FOO="bar")
def test_get_setting_raises_for_invalid_type():
    with pytest.raises(ValueError):
        _get_setting(int, "FOO", 1)
