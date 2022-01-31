import functools
import mimetypes
import os
import pathlib
import random
import unittest.mock
import uuid
from typing import Any
from typing import Callable
from typing import Dict
from typing import Type
from typing import TypeVar
from typing import Union
from typing import cast

import boto3
import moto
from django.conf import settings as django_settings
from django.utils.module_loading import import_string
from moto.core.models import MockAWS
from storages.backends.gcloud import GoogleCloudFile
from storages.backends.gcloud import GoogleCloudStorage
from typing_extensions import Final

from collectfast import settings
from collectfast.tests.mock import GCloudClientMock
from collectfast.tests.mock import GoogleCloudStorageBlobMock

static_dir: Final = pathlib.Path(django_settings.STATICFILES_DIRS[0])

F = TypeVar("F", bound=Callable[..., Any])


class CloudTestCase(unittest.TestCase):
    mock_s3: MockAWS
    gcloud_file_init: Any
    gcloud_client: Any


def make_test(func: F) -> Type[unittest.TestCase]:
    """
    Creates a class that inherits from `unittest.TestCase` with the decorated
    function as a method. Create tests like this:

    >>> fn = lambda x: 1337
    >>> @make_test
    ... def test_fn(case):
    ...     case.assertEqual(fn(), 1337)
    """
    case = type(
        func.__name__,
        (unittest.TestCase,),
        {func.__name__: func, "setUp": setUp, "tearDown": tearDown},
    )
    case.__module__ = func.__module__
    return case


def test_many(**mutations: Callable[[F], F]) -> Callable[[F], Type[unittest.TestCase]]:
    def test(func: F) -> Type[unittest.TestCase]:
        """
        Creates a class that inherits from `unittest.TestCase` with the decorated
        function as a method. Create tests like this:

        >>> fn = lambda x: 1337
        >>> @make_test
        ... def test_fn(case):
        ...     case.assertEqual(fn(), 1337)
        """
        case_dict: Dict[str, Union[F, Callable]] = {
            "test_%s" % mutation_name: mutation(func)
            for mutation_name, mutation in mutations.items()
        }
        case_dict["setUp"] = setUp
        case_dict["tearDown"] = tearDown

        case = type(func.__name__, (unittest.TestCase,), case_dict)
        case.__module__ = func.__module__
        return case

    return test


def create_static_file() -> pathlib.Path:
    """Write random characters to a file in the static directory."""
    path = static_dir / f"{uuid.uuid4().hex}.txt"
    path.write_text("".join(chr(random.randint(0, 64)) for _ in range(500)))
    return path


def clean_static_dir() -> None:
    for filename in os.listdir(static_dir.as_posix()):
        file = static_dir / filename
        if file.is_file():
            file.unlink()


def override_setting(name: str, value: Any) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
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


def override_storage_attr(name: str, value: Any) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
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


def create_bucket() -> None:
    s3 = boto3.client("s3", region_name=django_settings.AWS_S3_REGION_NAME)
    location = {"LocationConstraint": django_settings.AWS_S3_REGION_NAME}
    s3.create_bucket(
        Bucket=django_settings.AWS_STORAGE_BUCKET_NAME,
        CreateBucketConfiguration=location,
    )


def delete_bucket() -> None:
    s3 = boto3.resource("s3", region_name=django_settings.AWS_S3_REGION_NAME)
    bucket = s3.Bucket(django_settings.AWS_STORAGE_BUCKET_NAME)
    bucket.objects.delete()
    bucket.delete()


def setUp(case: CloudTestCase) -> None:
    def init_gcloud_file(self, name, mode, storage):
        self.name = name
        self.mime_type = mimetypes.guess_type(name)[0]
        self._mode = mode
        self._storage = storage
        self.blob = storage.bucket.get_blob(name)
        if not self.blob and "w" in mode:
            self.blob = GoogleCloudStorageBlobMock(
                self.name, storage.bucket, chunk_size=storage.blob_chunk_size
            )
        self._file = None
        self._is_dirty = False

    case.mock_s3 = moto.mock_s3()
    case.mock_s3.start()
    create_bucket()
    case.gcloud_client = unittest.mock.patch.object(
        GoogleCloudStorage, "client", GCloudClientMock()
    )
    case.gcloud_file_init = unittest.mock.patch.object(
        GoogleCloudFile, "__init__", init_gcloud_file
    )
    case.gcloud_file_init.start()
    case.gcloud_client.start()


def tearDown(case: CloudTestCase) -> None:
    delete_bucket()
    case.mock_s3.stop()
    case.gcloud_file_init.stop()
    case.gcloud_client.stop()
