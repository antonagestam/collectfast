Hi there 👋

I am looking for a maintainer to take over this project. I am longer working
with any project that uses the collectstatic framework and therefor can't be as
invested as a maintainer of this project should preferably be.

Please get in contact with me via issues if you are willing to take over.

# Collectfast

A faster collectstatic command.

[![Test Suite](https://github.com/antonagestam/collectfast/workflows/Test%20Suite/badge.svg)](https://github.com/antonagestam/collectfast/actions?query=workflow%3A%22Test+Suite%22+branch%3Amaster)
[![Static analysis](https://github.com/antonagestam/collectfast/workflows/Static%20analysis/badge.svg?branch=master)](https://github.com/antonagestam/collectfast/actions?query=workflow%3A%22Static+analysis%22+branch%3Amaster)
[![Test Coverage](https://api.codeclimate.com/v1/badges/ae25f7543fea0bbccb01/test_coverage)](https://codeclimate.com/github/antonagestam/collectfast/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/ae25f7543fea0bbccb01/maintainability)](https://codeclimate.com/github/antonagestam/collectfast/maintainability)

**Features**

- Efficiently decide what files to upload using cached checksums
- Parallel file uploads

**Supported Storage Backends**

- `storages.backends.s3boto3.S3Boto3Storage`
- `storages.backends.gcloud.GoogleCloudStorage`
- `django.core.files.storage.FileSystemStorage`

Running Django's `collectstatic` command can become painfully slow as more and
more files are added to a project, especially when heavy libraries such as
jQuery UI are included in source code. Collectfast customizes the builtin
`collectstatic` command, adding different optimizations to make uploading large
amounts of files much faster.


## Installation

Install the app using pip:

```bash
$ python3 -m pip install Collectfast
```

Make sure you have this in your settings file and add `'collectfast'` to your
`INSTALLED_APPS`, before `'django.contrib.staticfiles'`:

```python
STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
COLLECTFAST_STRATEGY = "collectfast.strategies.boto3.Boto3Strategy"
INSTALLED_APPS = (
    # ...
    "collectfast",
)
```

**Note:** `'collectfast'` must come before `'django.contrib.staticfiles'` in
`INSTALLED_APPS`.

**Note:** The boto strategy will set `preload_metadata` on the remote storage
to `True`, see [#30][issue-30].

[issue-30]: https://github.com/antonagestam/collectfast/issues/30

##### Upload Strategies

Collectfast Strategy|Storage Backend
---|---
collectfast.strategies.boto3.Boto3Strategy|storages.backends.s3boto3.S3Boto3Storage
collectfast.strategies.gcloud.GoogleCloudStrategy|storages.backends.gcloud.GoogleCloudStorage
collectfast.strategies.filesystem.FileSystemStrategy|django.core.files.storage.FileSystemStorage

Custom strategies can also be made for backends not listed above by
implementing the `collectfast.strategies.Strategy` ABC.


## Usage

Collectfast overrides Django's builtin `collectstatic` command so just run
`python manage.py collectstatic` as normal.

You can disable Collectfast by using the `--disable-collectfast` option or by
setting `COLLECTFAST_ENABLED = False` in your settings file.

### Setting Up a Dedicated Cache Backend

It's recommended to setup a dedicated cache backend for Collectfast. Every time
Collectfast does not find a lookup for a file in the cache it will trigger a
lookup to the storage backend, so it's recommended to have a fairly high
`TIMEOUT` setting.

Configure your dedicated cache with the `COLLECTFAST_CACHE` setting:

```python
CACHES = {
    "default": {
        # Your default cache
    },
    "collectfast": {
        # Your dedicated Collectfast cache
    },
}

COLLECTFAST_CACHE = "collectfast"
```

If `COLLECTFAST_CACHE` isn't set, the `default` cache will be used.

**Note:** Collectfast will never clean the cache of obsolete files. To clean
out the entire cache, use `cache.clear()`. [See docs for Django's cache
framework][django-cache].

**Note:** We recommend you to set the `MAX_ENTRIES` setting if you have more
than 300 static files, see [#47][issue-47].

[django-cache]: https://docs.djangoproject.com/en/stable/topics/cache/
[issue-47]: https://github.com/antonagestam/collectfast/issues/47

### Enable Parallel Uploads

The parallelization feature enables parallel file uploads using Python's
`concurrent.futures` module. Enable it by setting the `COLLECTFAST_THREADS`
setting.

To enable parallel uploads, a dedicated cache backend must be setup and it must
use a backend that is thread-safe, i.e. something other than Django's default
LocMemCache.

```python
COLLECTFAST_THREADS = 20
```


## Debugging

By default, Collectfast will suppress any exceptions that happens when copying
and let Django's `collectstatic` handle it. To debug those suppressed errors
you can set `COLLECTFAST_DEBUG = True` in your Django settings file.


## Contribution

Please feel free to contribute by using issues and pull requests. Discussion is
open and welcome.

### Testing

The test suite is built to run against live S3 and GCloud buckets. You can
disable live tests by setting `SKIP_LIVE_TESTS=true` or running `make
test-skip-live`. To run live tests locally you need to provide API credentials
to test against. Add the credentials to a file named `storage-credentials` in
the root of the project directory:

```bash
export AWS_ACCESS_KEY_ID='...'
export AWS_SECRET_ACCESS_KEY='...'
export GCLOUD_CREDENTIALS='{...}'  # Google Cloud credentials as JSON
```

Install test dependencies and target Django version:

```bash
python3 -m pip install -r test-requirements.txt
python3 -m pip install django==2.2
```

Run test suite:

```bash
make test
```

Code quality tools are broken out from test requirements because some of them
only install on Python >= 3.7.

```bash
python3 -m pip install -r lint-requirements.txt
```

Run linters and static type check:

```bash
make lint
```


## License

Collectfast is licensed under the MIT License, see LICENSE file for more
information.
