from unittest import mock
from unittest import TestCase

from django.core.files.storage import FileSystemStorage
from django.test import override_settings as override_django_settings

from collectfast.management.commands.collectstatic import Command
from collectfast.strategies.base import _RemoteStorage
from collectfast.strategies.base import HashStrategy
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import make_test
from collectfast.tests.utils import override_setting


class BaseTestStrategy(HashStrategy[FileSystemStorage]):
    _should_copy_file = None
    
    def __init__(self, remote_storage):
        super().__init__(remote_storage)
        self.post_copy_hook = mock.MagicMock()
    
    def get_remote_file_hash(self, prefixed_path):
        pass

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
    COLLECTFAST_STRATEGY="collectfast.tests.command.test_post_copy_hook.TrueTestStrategy",
    STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
)
def test_calls_post_copy_hook_true(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()

    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    
    cmd.strategy.post_copy_hook.assert_called_once()
    case.assertIsNotNone(cmd.strategy.post_copy_hook.call_args)
    case.assertIn('copied', cmd.strategy.post_copy_hook.call_args.kwargs)
    copied = cmd.strategy.post_copy_hook.call_args.kwargs['copied']
    case.assertTrue(copied)


@make_test
@override_django_settings(
    COLLECTFAST_STRATEGY="collectfast.tests.command.test_post_copy_hook.FalseTestStrategy",
    STATICFILES_STORAGE="django.core.files.storage.FileSystemStorage",
)
def test_calls_post_copy_hook_false(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()

    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    
    cmd.strategy.post_copy_hook.assert_called_once()
    case.assertIsNotNone(cmd.strategy.post_copy_hook.call_args)
    case.assertIn('copied', cmd.strategy.post_copy_hook.call_args.kwargs)
    copied = cmd.strategy.post_copy_hook.call_args.kwargs['copied']
    case.assertFalse(copied)
