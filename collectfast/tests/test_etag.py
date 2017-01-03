import unittest
import mock

from collectfast import etag
from collectfast import settings


def test(func):
    cls = type("Test{}".format(func.__name__), (unittest.TestCase, ))
    setattr(cls, func.__name__, func)
    return func


class TestGetCacheKey(unittest.TestCase):
    def test_get_cache_key(self):
        cache_key = etag.get_cache_key('/some/random/path')
        prefix_len = len(settings.cache_key_prefix)
        self.assertTrue(cache_key.startswith(settings.cache_key_prefix))
        self.assertEqual(32 + prefix_len, len(cache_key))


class TestGetRemoteEtag(unittest.TestCase):
    # INTEGRATION TEST
    # boto and bot3!!!
    pass


class TestGetEtag(unittest.TestCase):
    pass


class TestDestroyEtag(unittest.TestCase):
    pass


class TestGetFileHash(unittest.TestCase):
    pass


class TestHasMatchingEtag(unittest.TestCase):
    pass


class TestCopyFile(unittest.TestCase):
    pass
