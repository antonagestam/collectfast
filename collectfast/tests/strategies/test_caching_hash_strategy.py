import string
from unittest import mock
from unittest import TestCase

from django.core.files.storage import FileSystemStorage

from collectfast import settings
from collectfast.strategies.base import CachingHashStrategy
from collectfast.tests.utils import make_test


hash_characters = string.ascii_letters + string.digits


class Strategy(CachingHashStrategy[FileSystemStorage]):
    def __init__(self):
        # type: () -> None
        super().__init__(FileSystemStorage())

    def get_remote_file_hash(self, prefixed_path):
        # type: (str) -> None
        pass


@make_test
def test_get_cache_key(case):
    # type: (TestCase) -> None
    strategy = Strategy()
    cache_key = strategy.get_cache_key("/some/random/path")
    prefix_len = len(settings.cache_key_prefix)
    case.assertTrue(cache_key.startswith(settings.cache_key_prefix))
    case.assertEqual(32 + prefix_len, len(cache_key))
    expected_chars = hash_characters + "_"
    for c in cache_key:
        case.assertIn(c, expected_chars)


@make_test
def test_gets_and_invalidates_hash(case):
    # type: (TestCase) -> None
    strategy = Strategy()
    expected_hash = "hash"
    mocked = mock.MagicMock(return_value=expected_hash)
    # ignore due to monkey patching
    strategy.get_remote_file_hash = mocked  # type: ignore[assignment]

    # empty cache
    result_hash = strategy.get_cached_remote_file_hash("path", "prefixed_path")
    case.assertEqual(result_hash, expected_hash)
    mocked.assert_called_once_with("prefixed_path")

    # populated cache
    mocked.reset_mock()
    result_hash = strategy.get_cached_remote_file_hash("path", "prefixed_path")
    case.assertEqual(result_hash, expected_hash)
    mocked.assert_not_called()

    # test destroy_etag
    mocked.reset_mock()
    strategy.invalidate_cached_hash("path")
    result_hash = strategy.get_cached_remote_file_hash("path", "prefixed_path")
    case.assertEqual(result_hash, expected_hash)
    mocked.assert_called_once_with("prefixed_path")
