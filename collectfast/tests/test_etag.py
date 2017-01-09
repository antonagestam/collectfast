import string
import tempfile
import platform

from mock import patch
from django.contrib.staticfiles.storage import StaticFilesStorage
from storages.backends.s3boto import S3BotoStorage

from collectfast import etag
from collectfast import settings
from .utils import test

hash_characters = string.ascii_letters + string.digits


@test
def test_get_cache_key(case):
    cache_key = etag.get_cache_key('/some/random/path')
    prefix_len = len(settings.cache_key_prefix)
    case.assertTrue(cache_key.startswith(settings.cache_key_prefix))
    case.assertEqual(32 + prefix_len, len(cache_key))
    expected_chars = hash_characters + '_'
    for c in cache_key:
        case.assertIn(c, expected_chars)


@test
@patch("collectfast.etag.get_remote_etag")
def test_get_destroy_etag(case, mocked):
    mocked.return_value = expected_hash = 'hash'

    # empty cache
    h = etag.get_etag('storage', 'path', 'prefixed_path')
    case.assertEqual(h, expected_hash)
    mocked.assert_called_once_with('storage', 'prefixed_path')

    # populated cache
    mocked.reset_mock()
    h = etag.get_etag('storage', 'path', 'prefixed_path')
    case.assertEqual(h, expected_hash)
    mocked.assert_not_called()

    # test destroy_etag
    mocked.reset_mock()
    etag.destroy_etag('path')
    h = etag.get_etag('storage', 'path', 'prefixed_path')
    case.assertEqual(h, expected_hash)
    mocked.assert_called_once_with('storage', 'prefixed_path')


@test
def test_get_file_hash(case):
    # disable this test on appveyor until permissions issue is solved
    if platform.system() == 'Windows':
        return
    storage = StaticFilesStorage()
    with tempfile.NamedTemporaryFile(dir=storage.base_location) as f:
        f.write(b'spam')
        h = etag.get_file_hash(storage, f.name)
    case.assertEqual(len(h), 34)
    case.assertTrue(h.startswith('"'))
    case.assertTrue(h.endswith('"'))
    for c in h[1:-1]:
        case.assertIn(c, hash_characters)


@test
@patch('collectfast.etag.get_etag')
@patch('collectfast.etag.get_file_hash')
def test_has_matching_etag(case, mocked_get_etag, mocked_get_file_hash):
    mocked_get_etag.return_value = mocked_get_file_hash.return_value = 'hash'
    case.assertTrue(
        etag.has_matching_etag('rs', 'ss', 'path', 'prefixed_path'))
    mocked_get_etag.return_value = 'not same'
    case.assertFalse(
        etag.has_matching_etag('rs', 'ss', 'path', 'prefixed_path'))


@test
@patch('collectfast.etag.has_matching_etag')
@patch('collectfast.etag.destroy_etag')
def test_should_copy_file(case, mocked_destroy_etag, mocked_has_matching_etag):
    remote_storage = S3BotoStorage()

    mocked_has_matching_etag.return_value = True
    case.assertFalse(etag.should_copy_file(
        remote_storage, 'path', 'prefixed_path', 'source_storage'))
    mocked_destroy_etag.assert_not_called()

    mocked_has_matching_etag.return_value = False
    case.assertTrue(etag.should_copy_file(
        remote_storage, 'path', 'prefixed_path', 'source_storage'))
    mocked_destroy_etag.assert_called_once_with('path')
