import pathlib

from django.core.files.storage import FileSystemStorage


class TestFileSystemStorage(FileSystemStorage):
    def __init__(self):
        # type: () -> None
        output = str(pathlib.Path(__file__).parent / "fs-remote")
        super().__init__(location=output)
