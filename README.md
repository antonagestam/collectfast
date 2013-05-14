Collectfast
---

Custom collectstatic that uses etag and md5 digests to determine whether files
on S3 have changed.

Written by _millarm on _djangosnippets

For use with S3 BotoStorage:

    STATICFILES_STORAGE = "storages.backends.s3boto.S3BotoStorage"

and:

    AWS_PRELOAD_METADATA = True


Custom management command that compares the MD5 sum and etag from S3 and if the
two are the same skips file copy. This makes running collect static MUCH faster
if you are using git as a source control system which updates timestamps.

_djangosnippets = http://djangosnippets.org/snippets/2889/
_millarm = http://djangosnippets.org/users/millarm/