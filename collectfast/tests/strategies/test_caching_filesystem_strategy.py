from unittest import mock

from django.core.files.storage import FileSystemStorage

from collectfast.strategies.filesystem import CachingFileSystemStrategy
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import make_test


@make_test
def test_post_copy_hook_primes_cache(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()
    expected_hash = 'abc123'
    local_storage = FileSystemStorage()
    remote_storage = FileSystemStorage()
    strategy = CachingFileSystemStrategy(remote_storage)
    with patch.object(strategy, 'get_local_file_hash', return_value=expected_hash) as mock_get_local_file_hash:
        with patch.object(strategy, 'get_remote_file_hash') as mock_get_remote_file_hash:
            strategy.post_copy_hook(path.name, path.name, local_storage)
            actual_hash = strategy.get_cached_remote_file_hash(path.name, path.name)
            mock_get_remote_file_hash.assert_not_called()
            mock_get_local_file_hash.assert_called_once()
    case.assertEqual(actual_hash, expected_hash)
