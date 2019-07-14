import warnings


class BaseStorageExtensions(object):
    def __init__(self, storage):
        self.storage = storage

    def reset_connection(self):
        raise NotImplementedError('Defined by subclass')

    def get_remote_etag(self, prefixed_path):
        raise NotImplementedError('Defined by subclass')


def check_preload_metadata(storage):
    if storage.preload_metadata is not True:
        storage.preload_metadata = True
        warnings.warn(
            "Collectfast does not work properly without "
            "`preload_metadata` set to `True` on the storage class. Try "
            "setting `AWS_PRELOAD_METADATA` to `True`. Overriding "
            "`storage.preload_metadata` and continuing.")
