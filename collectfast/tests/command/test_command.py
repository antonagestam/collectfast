from unittest import mock
from unittest import TestCase

import pytest
from _pytest.fixtures import SubRequest
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings as override_django_settings
from pytest_django.fixtures import SettingsWrapper

from .utils import call_collectstatic
from collectfast.management.commands.collectstatic import Command
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import live_test
from collectfast.tests.utils import make_test
from collectfast.tests.utils import override_setting


gzip_backend_confs = [
    pytest.param(
        "storages.backends.s3boto3.S3StaticStorage",
        "collectfast.strategies.boto3.Boto3Strategy",
        marks=[
            pytest.mark.boto3,
            pytest.mark.skipif(
                not settings.AWS_ACCESS_KEY_ID, reason="AWS credentials are not set"
            ),
        ],
        id="boto3",
    ),
    pytest.param(
        "storages.backends.s3boto3.S3ManifestStaticStorage",
        "collectfast.strategies.boto3.Boto3Strategy",
        marks=[
            pytest.mark.boto3,
            pytest.mark.skipif(
                not settings.AWS_ACCESS_KEY_ID, reason="AWS credentials are not set"
            ),
        ],
        id="boto3-manifest",
    ),
    pytest.param(
        "swift.storage.StaticSwiftStorage",
        "collectfast.strategies.swift.OpenStackSwiftStrategy",
        marks=[
            pytest.mark.swift,
            pytest.mark.skipif(
                not settings.SWIFT_AUTH_URL,
                reason="Openstack Swift credentials are not set",
            ),
        ],
        id="swift",
    ),
]
all_backend_confs = gzip_backend_confs + [
    pytest.param(
        "django.core.files.storage.FileSystemStorage",
        "collectfast.strategies.filesystem.CachingFileSystemStrategy",
        marks=pytest.mark.filesystem,
        id="filesystem-caching",
    ),
    pytest.param(
        "django.core.files.storage.FileSystemStorage",
        "collectfast.strategies.filesystem.FileSystemStrategy",
        marks=pytest.mark.filesystem,
        id="filesystem",
    ),
    pytest.param(
        "storages.backends.gcloud.GoogleCloudStorage",
        "collectfast.strategies.gcloud.GoogleCloudStrategy",
        marks=[
            pytest.mark.gcloud,
            pytest.mark.skipif(
                not settings.GS_CREDENTIALS,
                reason="Google Cloud credentials are not set",
            ),
        ],
        id="gcloud",
    ),
]


@pytest.fixture
def gzip(storage: str) -> None:
    if "s3boto3" in storage:
        with mock.patch.object(staticfiles_storage, "gzip", True):
            yield
    elif "swift" in storage:
        if not hasattr(staticfiles_storage, "gzip_content_types"):
            pytest.skip("django-storage-swift release without gzip support")
        with mock.patch.object(
            staticfiles_storage, "gzip_content_types", ("text/plain",)
        ):
            yield


@pytest.fixture(scope="function")
def storage(settings: SettingsWrapper, request: SubRequest):
    if "swift" in request.param:
        pytest.importorskip("swift")  # Cannot be used with parametrize params.
    settings.STATICFILES_STORAGE = request.param
    return request.param


@pytest.fixture(scope="function")
def strategy(settings: SettingsWrapper, request: SubRequest):
    settings.COLLECTFAST_STRATEGY = request.param
    return request.param


@pytest.fixture(scope="module")
def case() -> TestCase:
    return TestCase()


@pytest.mark.parametrize("storage,strategy", all_backend_confs, indirect=True)
@live_test
def test_basics(case: TestCase, strategy: str, storage: str) -> None:
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic())
    # file state should now be cached
    case.assertIn("0 static files copied.", call_collectstatic())


@pytest.mark.parametrize("storage,strategy", all_backend_confs, indirect=True)
@live_test
@override_setting("threads", 5)
def test_threads(case: TestCase, strategy: str, storage: str) -> None:
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


@pytest.mark.parametrize("storage,strategy", gzip_backend_confs, indirect=True)
@live_test
@override_setting("aws_is_gzipped", True)
def test_gzip(case: TestCase, gzip: None, strategy: str, storage: str) -> None:
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


@pytest.mark.parametrize("storage,strategy", all_backend_confs, indirect=True)
@live_test
@mock.patch("collectfast.strategies.base.Strategy.post_copy_hook", autospec=True)
def test_calls_post_copy_hook(
    post_copy_hook: mock.MagicMock, case: TestCase, strategy: str, storage: str
) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    post_copy_hook.assert_called_once_with(mock.ANY, path.name, path.name, mock.ANY)


@pytest.mark.parametrize("storage,strategy", all_backend_confs, indirect=True)
@live_test
@mock.patch("collectfast.strategies.base.Strategy.on_skip_hook", autospec=True)
def test_calls_on_skip_hook(
    on_skip_hook: mock.MagicMock, case: TestCase, strategy: str, storage: str
) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    on_skip_hook.assert_not_called()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    on_skip_hook.assert_called_once_with(mock.ANY, path.name, path.name, mock.ANY)
