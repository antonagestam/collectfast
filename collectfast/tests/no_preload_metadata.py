from storages.backends.s3boto3 import S3Boto3Storage


class NPM(S3Boto3Storage):
    """
    Dummy class for testing that collectfast warns about overriding the
    `preload_metadata` attriute.
    """
    preload_metadata = False
