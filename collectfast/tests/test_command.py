"""
To test:

* Command.collect
    - Sets collect_time properly
    - Calls and returns value of super
* Command.get_cache_key
    - test return value (needs both 2.7 and 3.x)
* Command.get_lookup
    - Uses self.lookups if populated
    - Uses cache if populated
    - Properly calls storage.bucket.lookup
    - Properly populates cache and self.lookups
* Command.destroy_lookup
    - Properly deletes value from cache and self.lookups
* Command.copy_file
    - Respects self.ignore_etag and self.dry_run
    - Respects storage.location
    - Produces a proper md5 checksum
    - Returns False and increments self.num_skipped_files if matching checksums
    - Invalidates cache and self.lookups
    - Properly calls super
"""

from unittest import TestCase
from mock import patch

from ..management.commands.collectstatic import Command, cache


class TestCommand(TestCase):
    def setUp(self):
        cache.clear()

    def get_command(self, *args, **kwargs):
        return Command(*args, **kwargs)

    @patch("collectfast.management.commands.collectstatic.collectstatic"
           ".Command.collect")
    def test_collect(self, mocked_super):
        command = self.get_command()
        command.collect()
        self.assertEqual(command.num_skipped_files, 0)
        self.assertIsInstance(command.collect_time, str)

    def test_get_cache_key(self):
        command = self.get_command()
        cache_key = command.get_cache_key('/some/random/path')
        prefix_len = len(command.cache_key_prefix)
        self.assertTrue(cache_key.startswith(command.cache_key_prefix))
        self.assertEqual(32 + prefix_len, len(cache_key))

    @patch("collectfast.management.commands.collectstatic.cache.get")
    @patch("collectfast.management.commands.collectstatic.Command"
           ".get_storage_lookup")
    def mock_get_lookup(self, path, cached_value, mocked_lookup, mocked_cache):
        mocked_lookup.return_value = 'a fresh lookup'
        mocked_cache.return_value = cached_value
        command = self.get_command()
        ret_val = command.get_lookup(path)
        return ret_val, mocked_lookup, mocked_cache

    def get_fresh_lookup(self, path):
        return self.mock_get_lookup(path, False)

    def get_cached_lookup(self, path):
        return self.mock_get_lookup(path, 'a cached lookup')

    def test_get_lookup(self):
        path = '/some/unique/path'
        cache_key = self.get_command().get_cache_key(path)

        # Assert storage lookup is hit and cache is populated
        ret_val, mocked_lookup, mocked_cache = self.get_fresh_lookup(path)
        mocked_lookup.assert_called_once_with(path)
        self.assertEqual(ret_val, 'a fresh lookup')
        self.assertEqual(cache.get(cache_key), 'a fresh lookup')

        # Assert storage is not hit, but cache is
        ret_val, mocked_lookup, mocked_cache = self.get_cached_lookup(path)
        self.assertEqual(mocked_lookup.call_count, 0)
        self.assertEqual(mocked_cache.call_count, 1)
        self.assertEqual(ret_val, 'a cached lookup')

    @patch("collectfast.management.commands.collectstatic.Command"
           ".get_storage_lookup")
    def test_destroy_lookup(self, mocked_lookup):
        mocked_lookup.return_value = 'a fake lookup'
        c = self.get_command()
        path = '/another/unique/path'
        cache_key = c.get_cache_key(path)
        c.get_lookup(path)
        self.assertEqual(cache.get(cache_key), mocked_lookup.return_value)
        self.assertEqual(c.lookups[path], mocked_lookup.return_value)

        c.destroy_lookup(path)
        self.assertEqual(cache.get(cache_key, 'empty'), 'empty')
        self.assertNotIn(path, c.lookups)

    @patch("collectfast.management.commands.collectstatic.Command.get_lookup")
    def test_copy_file(self, mocked_lookup):
        c = self.get_command()
        c.execute(interactive=False)
        self.assertEqual(mocked_lookup.call_count, 1)