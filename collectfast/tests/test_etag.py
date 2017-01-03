import unittest
from unittest.mock import patch
import string

from collectfast import etag
from collectfast import settings


def test(func):
    """
    Creates a class that inherits from unittest.TestCase with func as a method.
    Create tests like this:

    >>> @test
    >>> def test_my_func(case):
    >>>     case.assertEqual(my_func(), 1337)
    """
    cls = type(func.__name__, (unittest.TestCase, ), {func.__name__: func})
    setattr(cls, func.__name__, func)
    return cls


@test
def test_get_cache_key(case):
    cache_key = etag.get_cache_key('/some/random/path')
    prefix_len = len(settings.cache_key_prefix)
    case.assertTrue(cache_key.startswith(settings.cache_key_prefix))
    case.assertEqual(32 + prefix_len, len(cache_key))
    expected_chars = string.ascii_letters + string.digits + '_'
    for c in cache_key:
        case.assertIn(c, expected_chars)


@test
@patch("collectfast.etag.get_remote_etag")
def test_get_destroy_etag(case, mocked):
    mocked.return_value = expected_hash = 'hash'

    # empty cache
    h = etag.get_etag('storage', 'path')
    case.assertEqual(h, expected_hash)
    mocked.assert_called_once_with('storage', 'path')

    # populated cache
    mocked.reset_mock()
    h = etag.get_etag('storage', 'path')
    case.assertEqual(h, expected_hash)
    mocked.assert_not_called()

    # test destroy_etag
    mocked.reset_mock()
    etag.destroy_etag('path')
    h = etag.get_etag('storage', 'path')
    case.assertEqual(h, expected_hash)
    mocked.assert_called_once_with('storage', 'path')



class TestGetRemoteEtag(unittest.TestCase):
    # INTEGRATION TEST
    # boto and bot3!!!
    pass

class TestGetFileHash(unittest.TestCase):
    pass


class TestHasMatchingEtag(unittest.TestCase):
    pass


class TestCopyFile(unittest.TestCase):
    pass
