import string
from unittest import mock
from unittest import TestCase

from django.core.files.storage import FileSystemStorage

from collectfast import settings
from collectfast.strategies.base import CachingHashStrategy
from collectfast.tests.utils import make_test


hash_characters = string.ascii_letters + string.digits


class Strategy(CachingHashStrategy[FileSystemStorage]):
    def __init__(self) -> None:
        super().__init__(FileSystemStorage())

    def get_remote_file_hash(self, prefixed_path: str) -> None:
        pass


@make_test
def test_get_cache_key(case: TestCase) -> None:
    strategy = Strategy()
    cache_key = strategy.get_cache_key("/some/random/path")
    prefix_len = len(settings.cache_key_prefix)
    case.assertTrue(cache_key.startswith(settings.cache_key_prefix))
    case.assertEqual(32 + prefix_len, len(cache_key))
    expected_chars = hash_characters + "_"
    for c in cache_key:
        case.assertIn(c, expected_chars)


@make_test
def test_gets_and_invalidates_hash(case: TestCase) -> None:
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


@make_test
def test_file_copied_hook_primes_cache(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()
    expected_hash = 'abc123'
    strategy = Strategy()
    with mock.patch.object(strategy, 'get_local_file_hash', return_value=expected_hash) as mock_get_local_file_hash:
        with mock.patch.object(strategy, 'get_remote_file_hash') as mock_get_remote_file_hash:
            strategy.file_copied_hook(path.name, path.name, local_storage)
            actual_hash = strategy.get_cached_remote_file_hash(path.name, path.name)
            mock_get_remote_file_hash.assert_not_called()
            mock_get_local_file_hash.assert_called_once()
    case.assertEqual(actual_hash, expected_hash)


@make_test
@mock.patch("collectfast.strategies.base.HashStrategy.get_local_file_hash")
def test_get_local_file_hash_memoization(case: TestCase, mocked_super_get_local_file_hash: mock.MagicMock) -> None:
    foo_hash = 'def456'
    mocked_super_get_local_file_hash.return_value = foo_hash
    strategy = Strategy()
    
    actual_hash = strategy.get_local_file_hash('foo', local_storage)
    case.assertEqual(actual_hash, foo_hash)
    
    actual_hash = strategy.get_local_file_hash('foo', local_storage)
    case.assertEqual(actual_hash, foo_hash)
    
    mocked_super_get_local_file_hash.assert_called_once_with('foo', local_storage)
    
    bar_hash = 'ghj789'
    mocked_super_get_local_file_hash.return_value = bar_hash
    
    actual_hash = strategy.get_local_file_hash('bar', local_storage)
    case.assertEqual(actual_hash, bar_hash)
    
    actual_hash = strategy.get_local_file_hash('bar', local_storage)
    case.assertEqual(actual_hash, bar_hash)
    
    mocked_super_get_local_file_hash.assert_called_with('bar', local_storage)
    case.assertEqual(mocked_super_get_local_file_hash.call_count, 2)
