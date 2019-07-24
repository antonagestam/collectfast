from django.utils.module_loading import import_string

STORAGE_EXTENSIONS_MAP = {
    # Maps the relevant `Storage` class to it corresponding `StorageExtensions` class
    'django.core.files.storage.FileSystemStorage': 'collectfast.storage_extensions.file_system.FileSystemStorageExtensions',
    'storages.backends.s3boto.S3BotoStorage': 'collectfast.storage_extensions.s3boto.S3BotoStorageExtensions',
    'storages.backends.s3boto3.S3Boto3Storage': 'collectfast.storage_extensions.s3boto3.S3Boto3StorageExtensions',
    'storages.backends.gcloud.GoogleCloudStorage': 'collectfast.storage_extensions.gcloud.GoogleCloudStorageExtensions',
}


def get_storage_extensions(storage):
    for storage_path, storage_extensions_path in STORAGE_EXTENSIONS_MAP.items():
        try:
            storage_class = import_string(storage_path)
            if isinstance(storage, storage_class):
                return import_string(storage_extensions_path)(storage)
        except:
            # Catch any error while importing storage class or storage extension class
            pass

    raise RuntimeError("No storage extension found for %s. Please register your storage extensions class in "
        "`STORAGE_EXTENSIONS_MAP`." % storage)
