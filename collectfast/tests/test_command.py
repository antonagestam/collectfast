from unittest import TestCase
from mock import patch
from django.core.files.storage import Storage
from os.path import join

from ..management.commands.collectstatic import Command, cache


class BotolikeStorage(Storage):
    location = None

    def _normalize_name(self, path):
        if self.location is not None:
            path = join(self.location, path)
        return path


class CollectfastTestCase(TestCase):
    def setUp(self):
        cache.clear()

    def get_command(self, *args, **kwargs):
        return Command(*args, **kwargs)


class TestCommand(CollectfastTestCase):
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

    def test_get_file_hash(self):
        self.assertTrue(False)


class TestCopyFile(CollectfastTestCase):
    def setUp(self):
        super(TestCopyFile, self).setUp()

    def tearDown(self):
        pass

    @patch("collectfast.management.commands.collectstatic.collectstatic.Command"
           ".copy_file")
    @patch("collectfast.management.commands.collectstatic.Command.get_lookup")
    def call_copy_file(self, mocked_lookup, mocked_copy_file_super, **kwargs):
        options = {
            "interactive": False,
            "post_process": False,
            "dry_run": False,
            "clear": False,
            "link": False,
            "ignore_patterns": [],
            "use_default_ignore_patterns": True}
        options.update(kwargs)
        path = options.pop('path', '/a/sweet/path')
        c = self.get_command()
        c.storage = options.pop('storage', BotolikeStorage())
        c.set_options(**options)
        ret_val = c.copy_file(path, path, c.storage)
        return ret_val, mocked_copy_file_super, mocked_lookup

    def test_respect_flags(self):
        """`copy_file` respects --ignore_etag and --dry_run flags"""
        path = '/a/sweet/path'
        storage = BotolikeStorage()

        ret_val, super_mock, lookup_mock = self.call_copy_file(
            path=path, storage=storage, ignore_etag=True)
        self.assertEqual(lookup_mock.call_count, 0)

        ret_val, super_mock, lookup_mock = self.call_copy_file(
            path=path, storage=storage, dry_run=True)
        self.assertEqual(lookup_mock.call_count, 0)

    def test_calls_super(self):
        """`copy_file` properly calls super method"""
        path = '/a/sweet/path'
        storage = BotolikeStorage()

        ret_val, super_mock, lookup_mock = self.call_copy_file(
            path=path, storage=storage)
        super_mock.assert_called_once_with(path, path, storage)
        self.assertFalse(ret_val is False)

    def test_skips(self):
        """
        Returns False and increments self.num_skipped_files if matching
        hashes
        """
        self.assertTrue(False)


    def test_invalidates_cache(self):
        """Invalidates cache and self.lookups"""
        self.assertTrue(False)