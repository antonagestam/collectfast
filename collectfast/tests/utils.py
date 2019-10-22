import functools
import os
import pathlib
import random
import unittest
import uuid
from typing import Any
from typing import Callable
from typing import cast
from typing import Type
from typing import TypeVar

from django.conf import settings as django_settings
from django.utils.module_loading import import_string
from typing_extensions import Final

from collectfast import settings

F = TypeVar("F", bound=Callable[..., Any])
static_dir = pathlib.Path(django_settings.STATICFILES_DIRS[0])  # type: Final


def make_test(func):
    # type: (F) -> Type[unittest.TestCase]
    """
    Creates a class that inherits from `unittest.TestCase` with the decorated
    function as a method. Create tests like this:

    >>> fn = lambda x: 1337
    >>> @make_test
    ... def test_fn(case):
    ...     case.assertEqual(fn(), 1337)
    """
    case = type(func.__name__, (unittest.TestCase,), {func.__name__: func})
    case.__module__ = func.__module__
    return case


def test_many(**mutations):
    # type: (Callable[[F], F]) -> Callable[[F], Type[unittest.TestCase]]
    def test(func):
        # type: (F) -> Type[unittest.TestCase]
        """
        Creates a class that inherits from `unittest.TestCase` with the decorated
        function as a method. Create tests like this:

        >>> fn = lambda x: 1337
        >>> @make_test
        ... def test_fn(case):
        ...     case.assertEqual(fn(), 1337)
        """
        case_dict = {
            "test_%s" % mutation_name: mutation(func)
            for mutation_name, mutation in mutations.items()
        }

        case = type(func.__name__, (unittest.TestCase,), case_dict)
        case.__module__ = func.__module__
        return case

    return test


def create_static_file():
    # type: () -> None
    """Write random characters to a file in the static directory."""
    filename = "%s.txt" % uuid.uuid4().hex
    with (static_dir / filename).open("w+") as file_:
        for _ in range(500):
            file_.write(chr(int(random.random() * 64)))


def clean_static_dir():
    # type: () -> None
    for filename in os.listdir(static_dir.as_posix()):
        file = static_dir / filename
        if file.is_file():
            file.unlink()


def override_setting(name, value):
    # type: (str, Any) -> Callable[[F], F]
    def decorator(fn):
        # type: (F) -> F
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            original = getattr(settings, name)
            setattr(settings, name, value)
            try:
                return fn(*args, **kwargs)
            finally:
                setattr(settings, name, original)

        return cast(F, wrapper)

    return decorator


def override_storage_attr(name, value):
    # type: (str, Any) -> Callable[[F], F]
    def decorator(fn):
        # type: (F) -> F
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            storage = import_string(django_settings.STATICFILES_STORAGE)
            original = getattr(storage, name)
            setattr(storage, name, value)
            try:
                return fn(*args, **kwargs)
            finally:
                setattr(storage, name, original)

        return cast(F, wrapper)

    return decorator
