import functools
import os
import random
import unittest
import uuid

from django.conf import settings as django_settings
from django.utils.module_loading import import_string

from collectfast import settings


def test(func):
    """
    Creates a class that inherits from `unittest.TestCase` with the decorated
    function as a method. Create tests like this:

    >>> fn = lambda x: 1337
    >>> @test
    >>> def test_fn(case):
    >>>     case.assertEqual(fn(), 1337)
    """
    return type(func.__name__, (unittest.TestCase,), {func.__name__: func})


def create_static_file():
    filename = "static/%s.txt" % uuid.uuid4()
    with open(filename, "w+") as f:
        for _ in range(500):
            f.write(chr(int(random.random() * 64)))
        f.close()


def clean_static_dir():
    d = "static/"
    for f in os.listdir(d):
        path = os.path.join(d, f)
        if os.path.isfile(path):
            os.unlink(path)


def override_setting(name, value):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            original = getattr(settings, name)
            setattr(settings, name, value)
            ret = fn(*args, **kwargs)
            setattr(settings, name, original)
            return ret

        return wrapper

    return decorator


def override_storage_attr(name, value):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            storage = import_string(getattr(django_settings, "STATICFILES_STORAGE"))
            original = getattr(storage, name)
            setattr(storage, name, value)
            ret = fn(*args, **kwargs)
            setattr(storage, name, original)
            return ret

        return wrapper

    return decorator
