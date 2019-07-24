import warnings


class BaseStorageExtensions(object):
    """
    Base class for extension methods not implemented in `Storage` but required
    for this project
    """
    def __init__(self, storage):
        self.storage = storage

    def reset_connection(self):
        pass

    def get_etag(self, path):
        raise NotImplementedError('Defined by subclass')

    def try_delete(self, path):
        self.storage.delete(path)


def check_preload_metadata(storage):
    if storage.preload_metadata is not True:
        storage.preload_metadata = True
        warnings.warn(
            "Collectfast does not work properly without "
            "`preload_metadata` set to `True` on the storage class. Try "
            "setting `AWS_PRELOAD_METADATA` to `True`. Overriding "
            "`storage.preload_metadata` and continuing.")
