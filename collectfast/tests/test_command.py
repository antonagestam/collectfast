# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from unittest import TestCase
from mock import patch
from os.path import join

from django.core.files.storage import Storage, FileSystemStorage
from django.core.files.base import ContentFile
from django.conf import settings

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
        self.path = '.collectfast-test-file.txt'
        self.storage = FileSystemStorage(location='./')

    def get_command(self, *args, **kwargs):
        return Command(*args, **kwargs)

    def tearDown(self):
        self.storage.delete(self.path)


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
           ".get_remote_etag")
    def mock_get_lookup(self, path, cached_value, mocked_lookup, mocked_cache):
        mocked_lookup.return_value = 'a fresh lookup'
        mocked_cache.return_value = cached_value
        command = self.get_command()
        ret_val = command.get_etag(path)
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
           ".get_remote_etag")
    def test_destroy_lookup(self, mocked_lookup):
        mocked_lookup.return_value = 'a fake lookup'
        c = self.get_command()
        path = '/another/unique/path'
        cache_key = c.get_cache_key(path)
        c.get_etag(path)
        self.assertEqual(cache.get(cache_key), mocked_lookup.return_value)
        self.assertEqual(c.etags[path], mocked_lookup.return_value)

        c.destroy_etag(path)
        self.assertEqual(cache.get(cache_key, 'empty'), 'empty')
        self.assertNotIn(path, c.etags)

    def test_make_sure_it_has_ignore_etag(self):
        command = self.get_command()
        parser = command.create_parser('', '')
        self.assertIn('ignore_etag', parser.parse_args())


class TestGetFileHash(CollectfastTestCase):
    def test_get_file_hash(self):
        content = 'this is some content to be hashed'
        expected_hash = '"16e71fd2be8be2a3a8c0be7b9aab6c04"'
        c = self.get_command()

        self.storage.save(self.path, ContentFile(content))
        file_hash = c.get_file_hash(self.storage, self.path)
        self.assertEqual(file_hash, expected_hash)

        self.storage.delete(self.path)

        self.storage.save(self.path, ContentFile('some nonsense'))
        file_hash = c.get_file_hash(self.storage, self.path)
        self.assertNotEqual(file_hash, expected_hash)


class TestCopyFile(CollectfastTestCase):
    @patch("collectfast.management.commands.collectstatic.collectstatic.Command"
           ".copy_file")
    @patch("collectfast.management.commands.collectstatic.Command.get_etag")
    def call_copy_file(self, mocked_lookup, mocked_copy_file_super, **kwargs):
        options = {
            "interactive": False,
            "verbosity": 1,
            "post_process": False,
            "dry_run": False,
            "clear": False,
            "link": False,
            "ignore_patterns": [],
            "use_default_ignore_patterns": True}
        options.update(kwargs)
        path = options.pop('path', '/a/sweet/path')

        if 'lookup_hash' in options:
            mocked_lookup.return_value = options.pop('lookup_hash')

        c = self.get_command()
        c.storage = options.pop('storage', BotolikeStorage())
        c.set_options(**options)
        c.num_skipped_files = 0
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

    @patch("collectfast.management.commands.collectstatic.Command"
           ".get_file_hash")
    @patch("collectfast.management.commands.collectstatic.Command"
           ".destroy_etag")
    def test_calls_super(self, mock_destroy_lookup, mock_get_file_hash):
        """`copy_file` properly calls super method"""
        path = '/a/sweet/path'
        storage = BotolikeStorage()

        ret_val, super_mock, lookup_mock = self.call_copy_file(
            path=path, storage=storage)
        super_mock.assert_called_once_with(path, path, storage)
        self.assertFalse(ret_val is False)
        mock_destroy_lookup.assert_called_once_with(path)

    @patch("collectfast.management.commands.collectstatic.Command"
           ".get_file_hash")
    def test_skips(self, mock_get_file_hash):
        """
        Returns False and increments self.num_skipped_files if matching
        hashes
        """
        # mock get_file_hash and lookup to return the same hashes
        mock_hash = 'thisisafakehash'
        mock_get_file_hash.return_value = mock_hash

        storage = BotolikeStorage()

        ret_val, super_mock, lookup_mock = self.call_copy_file(
            path=self.path, storage=storage, lookup_hash=mock_hash)
        self.assertFalse(ret_val)
        self.assertEqual(super_mock.call_count, 0)


class TestAwsPreloadMetadata(CollectfastTestCase):
    def setUp(self):
        super(TestAwsPreloadMetadata, self).setUp()
        settings.AWS_PRELOAD_METADATA = False

    def tearDown(self):
        super(TestAwsPreloadMetadata, self).tearDown()
        settings.AWS_PRELOAD_METADATA = True

    @patch(
        "collectfast.management.commands.collectstatic.Command._pre_setup_log")
    def test_always_true(self, _mock_log):
        c = self.get_command()
        self.assertTrue(c.storage.preload_metadata)

    @patch(
        "collectfast.management.commands.collectstatic.Command._pre_setup_log")
    def test_log(self, mock_log):
        self.get_command()
        mock_log.assert_called_once_with(
            "----> WARNING!\nCollectfast does not work properly without "
            "`AWS_PRELOAD_METADATA` set to `True`.\nOverriding "
            "`storage.preload_metadata` and continuing.")
