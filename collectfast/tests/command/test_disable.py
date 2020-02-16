from unittest import mock
from unittest import TestCase

from django.test import override_settings as override_django_settings

from .utils import call_collectstatic
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import live_test
from collectfast.tests.utils import make_test
from collectfast.tests.utils import override_setting


@make_test
@override_django_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
def test_disable_collectfast_with_default_storage(case: TestCase) -> None:
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied", call_collectstatic(disable_collectfast=True))


@make_test
@live_test
def test_disable_collectfast(case: TestCase) -> None:
    clean_static_dir()
    create_static_file()
    case.assertIn("1 static file copied.", call_collectstatic(disable_collectfast=True))


@override_setting("enabled", False)
@mock.patch("collectfast.management.commands.collectstatic.Command._load_strategy")
def test_no_load_with_disable_setting(mocked_load_strategy: mock.MagicMock) -> None:
    clean_static_dir()
    call_collectstatic()
    mocked_load_strategy.assert_not_called()


@mock.patch("collectfast.management.commands.collectstatic.Command._load_strategy")
def test_no_load_with_disable_flag(mocked_load_strategy: mock.MagicMock) -> None:
    clean_static_dir()
    call_collectstatic(disable_collectfast=True)
    mocked_load_strategy.assert_not_called()
