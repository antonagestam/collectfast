from unittest import mock
from unittest import TestCase

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings as override_django_settings

from .utils import call_collectstatic
from collectfast.management.commands.collectstatic import Command
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import live_test
from collectfast.tests.utils import make_test
from collectfast.tests.utils import override_setting
from collectfast.tests.utils import override_storage_attr
from collectfast.tests.utils import test_many


aws_backend_confs = {
    "boto3": override_django_settings(
        STATICFILES_STORAGE="storages.backends.s3boto3.S3Boto3Storage",
        COLLECTFAST_STRATEGY="collectfast.strategies.boto3.Boto3Strategy",
    ),
}
all_backend_confs = {
    **aws_backend_confs,
    "gcloud": override_django_settings(
        STATICFILES_STORAGE="storages.backends.gcloud.GoogleCloudStorage",
        COLLECTFAST_STRATEGY="collectfast.strategies.gcloud.GoogleCloudStrategy",
    ),
    "filesystem": override_django_settings(
        STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
        COLLECTFAST_STRATEGY="collectfast.strategies.filesystem.FileSystemStrategy",
    ),
    "cachingfilesystem": override_django_settings(
        STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
        COLLECTFAST_STRATEGY=(
            "collectfast.strategies.filesystem.CachingFileSystemStrategy"
        ),
    ),
}

make_test_aws_backends = test_many(**aws_backend_confs)
make_test_all_backends = test_many(**all_backend_confs)


@make_test_all_backends
@live_test
def test_basics(case: TestCase) -> None:
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic())
    # file state should now be cached
    case.assertIn("0 static files copied.", call_collectstatic())


@make_test_all_backends
@live_test
@override_setting("threads", 5)
def test_threads(case: TestCase) -> None:
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic())
    # file state should now be cached
    case.assertIn("0 static files copied.", call_collectstatic())


@make_test
def test_dry_run(case: TestCase) -> None:
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
@live_test
@override_storage_attr("gzip", True)
@override_setting("aws_is_gzipped", True)
def test_aws_is_gzipped(case: TestCase) -> None:
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic())
    # file state should now be cached
    case.assertIn("0 static files copied.", call_collectstatic())


@make_test
@override_django_settings(STATICFILES_STORAGE=None, COLLECTFAST_STRATEGY=None)
def test_raises_for_no_configured_strategy(case: TestCase) -> None:
    with case.assertRaises(ImproperlyConfigured):
        Command._load_strategy()


@make_test_all_backends
@live_test
@mock.patch("collectfast.strategies.base.Strategy.post_copy_hook", autospec=True)
def test_calls_post_copy_hook(_case: TestCase, post_copy_hook: mock.MagicMock) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    post_copy_hook.assert_called_once_with(mock.ANY, path.name, path.name, mock.ANY)


@make_test_all_backends
@live_test
@mock.patch("collectfast.strategies.base.Strategy.on_skip_hook", autospec=True)
def test_calls_on_skip_hook(_case: TestCase, on_skip_hook: mock.MagicMock) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    on_skip_hook.assert_not_called()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    on_skip_hook.assert_called_once_with(mock.ANY, path.name, path.name, mock.ANY)
