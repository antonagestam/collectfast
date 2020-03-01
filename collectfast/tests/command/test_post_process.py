from unittest import mock

from django.contrib.staticfiles.storage import StaticFilesStorage
from django.test import override_settings as override_django_settings

from collectfast.management.commands.collectstatic import Command
from collectfast.tests.utils import clean_static_dir
from collectfast.tests.utils import create_static_file
from collectfast.tests.utils import override_setting


class MockPostProcessing(StaticFilesStorage):
    def __init__(self):
        super().__init__()
        self.post_process = mock.MagicMock()


@override_setting("threads", 2)
@override_django_settings(
    STATICFILES_STORAGE="collectfast.tests.command.test_post_process.MockPostProcessing"
)
def test_calls_post_process_with_collected_files() -> None:
    clean_static_dir()
    path = create_static_file()

    cmd = Command()
    cmd.run_from_argv(["manage.py", "collectstatic", "--noinput"])
    cmd.storage.post_process.assert_called_once_with(
        {path.name: (mock.ANY, path.name)}, dry_run=False
    )
