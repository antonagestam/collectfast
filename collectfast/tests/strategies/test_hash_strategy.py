import re
import tempfile
from unittest import mock
from unittest import TestCase

from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.storage import FileSystemStorage

from collectfast.strategies.base import HashStrategy
from collectfast.tests.utils import make_test


class Strategy(HashStrategy[FileSystemStorage]):
    def __init__(self) -> None:
        super().__init__(FileSystemStorage())

    def get_remote_file_hash(self, prefixed_path: str) -> None:
        pass


@make_test
def test_get_file_hash(case: TestCase) -> None:
    strategy = Strategy()
    local_storage = StaticFilesStorage()

    with tempfile.NamedTemporaryFile(dir=local_storage.base_location) as f:
        f.write(b"spam")
        hash_ = strategy.get_local_file_hash(f.name, local_storage)
    case.assertTrue(re.fullmatch(r"^[A-z0-9]{32}$", hash_) is not None)


@make_test
def test_should_copy_file(case: TestCase) -> None:
    strategy = Strategy()
    local_storage = StaticFilesStorage()
    remote_hash = "foo"
    mock_remote_hash = mock.patch.object(
        strategy, "get_remote_file_hash", mock.MagicMock(return_value=remote_hash)
    )

    with mock_remote_hash:
        with mock.patch.object(
            strategy, "get_local_file_hash", mock.MagicMock(return_value=remote_hash)
        ):
            case.assertFalse(
                strategy.should_copy_file("path", "prefixed_path", local_storage)
            )
        with mock.patch.object(
            strategy, "get_local_file_hash", mock.MagicMock(return_value="bar")
        ):
            case.assertTrue(
                strategy.should_copy_file("path", "prefixed_path", local_storage)
            )
