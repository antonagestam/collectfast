from unittest import mock
from unittest import TestCase

from django.core.files.storage import FileSystemStorage
from django.test import override_settings as override_django_settings

from collectfast.management.commands.collectstatic import Command
from collectfast.strategies.base import Strategy
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import make_test

from .test_command import live_test
from .test_command import make_test_all_backends


class BaseTestStrategy(Strategy[FileSystemStorage]):
    _should_copy_file = None

    def __init__(self, remote_storage):
        super().__init__(remote_storage)
        self.file_copied_hook = mock.MagicMock()
        self.copy_skipped_hook = mock.MagicMock()

    def should_copy_file(
        self, path, prefixed_path, local_storage
    ):
        return self._should_copy_file


class TrueTestStrategy(BaseTestStrategy):
    _should_copy_file = True


class FalseTestStrategy(BaseTestStrategy):
    _should_copy_file = False


@make_test
@override_django_settings(
    COLLECTFAST_STRATEGY="collectfast.tests.command.test_copy_hooks.TrueTestStrategy",  # noqa: E501
    STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
)
def test_calls_file_copied_hook_simple(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    cmd.strategy.file_copied_hook.assert_called_once_with(
        path.name,
        path.name,
        mock.ANY,
    )


@make_test
@override_django_settings(
    COLLECTFAST_STRATEGY="collectfast.tests.command.test_copy_hooks.TrueTestStrategy",  # noqa: E501
    STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
)
def test_calls_copy_skipped_hook_collectstatic(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    cmd.collect()
    cmd.strategy.copy_skipped_hook.assert_called_once_with(
        path.name,
        path.name,
        mock.ANY,
    )


@make_test
@override_django_settings(
    COLLECTFAST_STRATEGY="collectfast.tests.command.test_copy_hooks.FalseTestStrategy",  # noqa: E501
    STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
)
def test_calls_copy_skipped_hook_collectfast(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    cmd.strategy.copy_skipped_hook.assert_called_once_with(
        path.name,
        path.name,
        mock.ANY,
    )


@make_test_all_backends
@live_test
def test_call_file_copied_hook_all_backends(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    cmd.strategy.file_copied_hook.assert_called_once_with(
        path.name,
        path.name,
        mock.ANY,
    )


@make_test_all_backends
@live_test
def test_call_copy_skipped_hook_all_backends(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()
    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    cmd.collect()
    cmd.strategy.copy_skipped_hook.assert_called_once_with(
        path.name,
        path.name,
        mock.ANY,
    )
