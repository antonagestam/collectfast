from unittest import TestCase

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings as override_django_settings

from .utils import call_collectstatic
from collectfast.management.commands.collectstatic import Command
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import make_test
from collectfast.tests.utils import override_setting
from collectfast.tests.utils import override_storage_attr
from collectfast.tests.utils import test_many


aws_backend_confs = {
    "boto3": override_django_settings(
        STATICFILES_STORAGE="storages.backends.s3boto3.S3Boto3Storage",
        COLLECTFAST_STRATEGY="collectfast.strategies.boto3.Boto3Strategy",
    ),
    "boto": override_django_settings(
        STATICFILES_STORAGE="storages.backends.s3boto.S3BotoStorage",
        COLLECTFAST_STRATEGY="collectfast.strategies.boto.BotoStrategy",
    ),
}
# use PEP448-style unpacking instead of copy+update once 3.4 support is dropped
all_backend_confs = aws_backend_confs.copy()
all_backend_confs.update(
    {
        "gcloud": override_django_settings(
            STATICFILES_STORAGE="storages.backends.gcloud.GoogleCloudStorage",
            COLLECTFAST_STRATEGY="collectfast.strategies.gcloud.GoogleCloudStrategy",
        ),
        "filesystem": override_django_settings(
            STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
            COLLECTFAST_STRATEGY="collectfast.strategies.filesystem.FileSystemStrategy",
        ),
    }
)

make_test_aws_backends = test_many(**aws_backend_confs)
make_test_all_backends = test_many(**all_backend_confs)


@make_test_all_backends
def test_basics(case):
    # type: (TestCase) -> None
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic())
    # file state should now be cached
    case.assertIn("0 static files copied.", call_collectstatic())


@make_test_all_backends
@override_setting("threads", 5)
def test_threads(case):
    # type: (TestCase) -> None
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic())
    # file state should now be cached
    case.assertIn("0 static files copied.", call_collectstatic())


@make_test
def test_dry_run(case):
    # type: (TestCase) -> None
    clean_static_dir()
    create_static_file()
    result = call_collectstatic(dry_run=True)
    case.assertIn("1 static file copied.", result)
    case.assertTrue("Pretending to copy", result)
    result = call_collectstatic(dry_run=True)
    case.assertIn("1 static file copied.", result)
    case.assertTrue("Pretending to copy", result)
    case.assertTrue("Pretending to delete", result)


@make_test_aws_backends
@override_storage_attr("gzip", True)
@override_setting("aws_is_gzipped", True)
def test_aws_is_gzipped(case):
    # type: (TestCase) -> None
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic())
    # file state should now be cached
    case.assertIn("0 static files copied.", call_collectstatic())


@make_test
@override_django_settings(
    STATICFILES_STORAGE="storages.backends.s3boto.S3BotoStorage",
    COLLECTFAST_STRATEGY=None,
)
def test_recognizes_boto_storage(case):
    # type: (TestCase) -> None
    case.assertEqual(Command._load_strategy().__name__, "BotoStrategy")


@make_test
@override_django_settings(
    STATICFILES_STORAGE="storages.backends.s3boto3.S3Boto3Storage",
    COLLECTFAST_STRATEGY=None,
)
def test_recognizes_boto3_storage(case):
    # type: (TestCase) -> None
    case.assertEqual(Command._load_strategy().__name__, "Boto3Strategy")


@make_test
@override_django_settings(STATICFILES_STORAGE=None, COLLECTFAST_STRATEGY=None)
def test_raises_for_unrecognized_storage(case):
    # type: (TestCase) -> None
    with case.assertRaises(ImproperlyConfigured):
        Command._load_strategy()
