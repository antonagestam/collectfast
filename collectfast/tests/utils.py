import random
import unittest
import uuid
import os
import functools

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
    return type(func.__name__, (unittest.TestCase, ), {func.__name__: func})


def create_static_file():
    filename = 'static/%s.txt' % uuid.uuid4()
    for i in range(3):
        with open(filename, 'w+') as f:
            for i in range(500):
                f.write(chr(int(random.random() * 64)))
            f.close()


def clean_static_dir():
    d = 'static/'
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
