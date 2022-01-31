import hashlib
import pathlib
from typing import Any
from typing import Dict
from typing import Optional

from django.conf import settings as django_settings
from django.core.files import File
from google.cloud.exceptions import NotFound
from typing_extensions import Final

static_dir: Final = pathlib.Path(django_settings.STATICFILES_DIRS[0])


class GCloudClientMock:
    _http = None
    _connection = type("ConnectionMock", (), {"API_BASE_URL": "example.com"})

    def bucket(
        self, bucket_name: str, user_project: Optional[str] = None
    ) -> "GoogleCloudStorageBucketMock":
        return GoogleCloudStorageBucketMock(
            client=self,
            name=bucket_name,
            user_project=user_project,
        )


class GoogleCloudStorageBucketMock:
    def __init__(
        self,
        client: GCloudClientMock,
        name: Optional[str] = None,
        user_project: Optional[str] = None,
    ) -> None:
        self.client = client
        self.name = name
        self.user_project = user_project
        self.saved_files: Dict[str, File] = {}

    def get_blob(self, path: str) -> Optional["GoogleCloudStorageBlobMock"]:
        blob = GoogleCloudStorageBlobMock(path, self)
        try:
            blob.reload()
        except FileNotFoundError:
            return None
        return blob

    def delete_blob(self, name: str) -> None:
        if name not in self.saved_files:
            raise NotFound("not found")
        del self.saved_files[name]

    def save_blob(self, name: str, file_obj: File) -> None:
        self.saved_files[name] = file_obj


class GoogleCloudStorageBlobMock:
    def __init__(
        self,
        name: str,
        bucket: GoogleCloudStorageBucketMock,
        chunk_size: Optional[int] = None,
        encryption_key: Optional[str] = None,
        kms_key_name: Optional[str] = None,
        generation: Optional[str] = None,
    ):
        self._bucket = bucket
        self.name = name
        self.generation = generation
        self.chunk_size = chunk_size
        self.encryption_key = encryption_key
        self.kms_key_name = kms_key_name
        self._properties: Dict[str, Any] = {}

    @property
    def bucket(self) -> GoogleCloudStorageBucketMock:
        return self._bucket

    def upload_from_file(
        self,
        file_obj: File,
        **_: Dict[str, Any],
    ) -> None:
        self.bucket.save_blob(self.name, file_obj)

    def reload(self) -> None:
        if self.name not in self.bucket.saved_files:
            raise FileNotFoundError
        f = self.bucket.saved_files[self.name]
        contents: bytes = f.read()
        file_hash: str = hashlib.md5(contents).hexdigest()
        self._properties["md5Hash"] = file_hash
