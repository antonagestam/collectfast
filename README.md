Collectfast
===========

The fast `collectstatic` for Django-apps with S3 as storage backend.

Custom management command that compares the MD5 sum and etag from S3 and if the
two are the same skips file copy. This makes running collect static MUCH faster
if you are using git as a source control system which updates timestamps.

Installation
------------

Install the app using pip:

    pip install -e git+https://github.com/antonagestam/collectfast.git@0.1.1#egg=collectfast

Make sure you have this in your settings file and add `'collectfast'` to
your `INSTALLED_APPS`:

    STATICFILES_STORAGE = "storages.backends.s3boto.S3BotoStorage"
    AWS_PRELOAD_METADATA = True
    INSTALLED_APPS = (
        …
        'collectfast',
    )

Usage
-----

Collectfast overrides Django's builtin `collectstatic` command so just run
`python manage.py collectstatic` as normal. You can disable collectfast
by using the `--ignore_etag` option.

Cred
----

Original idea stolen from [djangosnippets](http://djangosnippets.org/snippets/2889/)
