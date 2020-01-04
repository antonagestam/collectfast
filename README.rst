Collectfast
===========

A faster collectstatic command.

|Build Status| |Coverage Status|

**Features**

- Compares and caches file checksums before uploading
- Parallelizes file uploads using Python's multiprocessing module

**Supported Storage Backends**

- ``storages.backends.s3boto.S3BotoStorage`` (deprecated, will be removed in 2.0)
- ``storages.backends.s3boto3.S3Boto3Storage``
- ``storages.backends.gcloud.GoogleCloudStorage``
- ``django.core.files.storage.FileSystemStorage``

Running Django's ``collectstatic`` command can become painfully slow as more
and more files are added to a project, especially when heavy libraries such as
jQuery UI are included in source code. Collectfast customizes the builtin
``collectstatic`` command, adding different optimizations to make uploading
large amounts of files much faster.


Installation
------------

Install the app using pip:

::

    $ pip install Collectfast

Make sure you have this in your settings file and add ``'collectfast'`` to your
``INSTALLED_APPS``, before ``'django.contrib.staticfiles'``:

.. code:: python

    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    COLLECTFAST_STRATEGY = "collectfast.strategies.boto3.Boto3Strategy"
    INSTALLED_APPS = (
        # ...
        'collectfast',
    )

**Note:** ``'collectfast'`` must come before ``'django.contrib.staticfiles'`` in
``INSTALLED_APPS``.

**Note:** Boto strategies will set ``preload_metadata`` on the remote storage to
``True``, see `#30 <https://github.com/antonagestam/collectfast/issues/30>`_.


Supported Strategies
~~~~~~~~~~~~~~~~~~~~

+--------------------------------------------------------+-----------------------------------------------+
|Strategy class                                          |Storage class                                  |
+========================================================+===============================================+
|``collectfast.strategies.boto.BotoStrategy``            |``storages.backends.s3boto.S3BotoStorage``     |
+--------------------------------------------------------+-----------------------------------------------+
|``collectfast.strategies.boto3.Boto3Strategy``          |``storages.backends.s3boto3.S3Boto3Storage``   |
+--------------------------------------------------------+-----------------------------------------------+
|``collectfast.strategies.gcloud.GoogleCloudStrategy``   |``storages.backends.gcloud.GoogleCloudStorage``|
+--------------------------------------------------------+-----------------------------------------------+
|``collectfast.strategies.filesystem.FileSystemStrategy``|``django.core.files.storage.FileSystemStorage``|
+--------------------------------------------------------+-----------------------------------------------+


Usage
-----

Collectfast overrides Django's builtin ``collectstatic`` command so just run
``python manage.py collectstatic`` as normal. You can disable Collectfast by
using the ``--disable-collectfast`` option.

You can also disable Collectfast by setting ``COLLECTFAST_ENABLED = False`` in
your settings file. This is useful when using a local file storage backend for
development.


Setup Dedicated Cache Backend
-----------------------------

It's recommended to setup a dedicated cache backend for Collectfast. Every
time Collectfast does not find a lookup for a file in the cache it will trigger
a lookup to the storage backend, so it's recommended to have a fairly high
``TIMEOUT`` setting.

Set up your dedicated cache in settings.py with the ``COLLECTFAST_CACHE``
setting:

.. code:: python

    CACHES = {
        'default': {
            # Your default cache
        },
        'collectfast': {
            # Your dedicated Collectfast cache
        }
    }

    COLLECTFAST_CACHE = 'collectfast'

By default Collectfast will use the ``default`` cache.

**Note:** Collectfast will never clean the cache of obsolete files. To clean
out the entire cache, use ``cache.clear()``. `Read more about Django's cache
framework. <https://docs.djangoproject.com/en/stable/topics/cache/>`_

**Note:** We recommend you to set the ``MAX_ENTRIES`` setting if you have more
than 300 static files, see `#47
<https://github.com/antonagestam/collectfast/issues/47>`_


Enable Parallelization
----------------------

The parallelization feature enables parallel file uploads using Python's
multiprocessing module. Enable it by setting the ``COLLECTFAST_THREADS``
setting.

To enable parallelization of file copying, a dedicated cache backend must be
setup and it must use a backend that is threadsafe, i.e. something other than
Django's default LocMemCache.

.. code:: python

    COLLECTFAST_THREADS = 20


Debug
-----

By default, Collectfast will suppress any exceptions that happens when copying
and let Django's ``collectstatic`` handle it. To debug those suppressed errors
you can set ``COLLECTFAST_DEBUG = True`` in your Django settings file.


Contribution
------------

Please feel free to contribute by using issues and pull requests. Discussion is
open and welcome.

**Testing**

The test suite is built to run against live S3 and GCloud buckets. You can disable live
tests by setting `SKIP_LIVE_TESTS=true` or running `make test-skip-live`. To run live
tests locally you need to provide API credentials to test against. Add the credentials
to a file named `storage-credentials` in the root of the project directory:

.. code:: bash

    export AWS_ACCESS_KEY_ID='...'
    export AWS_SECRET_ACCESS_KEY='...'
    export GCLOUD_CREDENTIALS='{...}'  # Google Cloud credentials as JSON

Install test dependencies and target Django version:

.. code:: bash

    pip install -r test-requirements.txt
    pip install django==2.2

Run test suite:

.. code:: bash

    make test

Code quality tools are broken out from test requirements because some of them
only install on Python >= 3.7.

.. code:: bash

    pip install -r lint-requirements.txt

Run linters and static type check:

.. code:: bash

    make lint


License
-------

Collectfast is licensed under the MIT License, see LICENSE file for more
information.


.. |Build Status| image:: https://api.travis-ci.org/antonagestam/collectfast.svg?branch=master
   :target: https://travis-ci.org/antonagestam/collectfast
.. |Coverage Status| image:: https://coveralls.io/repos/github/antonagestam/collectfast/badge.svg?branch=master
   :target: https://coveralls.io/github/antonagestam/collectfast?branch=master
