from unittest import mock
from unittest import TestCase

from django.test import override_settings as override_django_settings

from collectfast.management.commands.collectstatic import Command
from collectfast.strategies.base import Strategy
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import make_test
from collectfast.tests.utils import override_setting


class BaseTestStrategy(Strategy):
    _should_copy_file = None
    
    def __init__(self):
        super().__init__()
        self.post_copy_hook = mock.MagicMock()
    
    def should_copy_file(
        self, path, prefixed_path, local_storage
    ):
        return self._should_copy_file


class TrueTestStrategy(Strategy):
    _should_copy_file = True


class FalseTestStrategy(Strategy):
    _should_copy_file = False
    

@override_django_settings(
    COLLECTFAST_STRATEGY="collectfast.tests.command.test_post_copy_hook.TrueTestStrategy"
)
@make_test
def test_calls_post_copy_hook_true(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()

    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    
    cmd.strategy.post_copy_hook.assert_called_once()
    case.assertNotNone(cmd.strategy.post_copy_hook.call_args)
    case.assertIn('copied', cmd.strategy.post_copy_hook.call_args.kwargs)
    copied = cmd.strategy.post_copy_hook.call_args.kwargs['copied']
    case.assertTrue(copied)


@override_django_settings(
    COLLECTFAST_STRATEGY="collectfast.tests.command.test_post_copy_hook.FaleTestStrategy"
)
@make_test
def test_calls_post_copy_hook_false(case: TestCase) -> None:
    clean_static_dir()
    path = create_static_file()

    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    
    cmd.strategy.post_copy_hook.assert_called_once()
    case.assertNotNone(cmd.strategy.post_copy_hook.call_args)
    case.assertIn('copied', cmd.strategy.post_copy_hook.call_args.kwargs)
    copied = cmd.strategy.post_copy_hook.call_args.kwargs['copied']
    case.assertFalse(copied)
