Collectfast – A Faster Collectstatic
====================================

|Jazzband| |Build Status| |Windows Build Status| |Coverage Status|

The fast ``collectstatic`` for Django projects with S3 as storage
backend.

**Features**

- Comparing and caching of md5 checksums before uploading
- Parallel file uploads using Python's multiprocessing module

Running Django's ``collectstatic`` command can become really slow as
more and more files are added to a project, especially if heavy
libraries such as jQuery UI are included in the source. This is a custom
management command that compares the md5 sum of files with S3 and
completely ignores ``modified_time``. The results of the hash lookups
are cached locally using your default Django cache. This can make
deploying much faster!


Installation
------------

Install the app using pip:

::

    $ pip install Collectfast

Make sure you have this in your settings file and add ``'collectfast'``
to your ``INSTALLED_APPS``:

.. code:: python

    STATICFILES_STORAGE = "storages.backends.s3boto.S3BotoStorage"
    AWS_PRELOAD_METADATA = True
    INSTALLED_APPS = (
        # …
        'collectfast',
    )

``'collectfast'`` should come before ``'django.contrib.staticfiles'``.
Please note, that failure to do so will cause Django to use
``django.contrib.staticfiles``'s ``collectstatic``.

**Note:** ``preload_metadata`` of the storage class will be overwritten
even if ``AWS_PRELOAD_METADATA`` is not set to True see
`#30 <https://github.com/jazzband/collectfast/issues/30>`_


Usage
-----

Collectfast overrides Django's builtin ``collectstatic`` command so just
run ``python manage.py collectstatic`` as normal. You can disable
Collectfast by using the ``--disable-collectfast`` option.

You can also disable collectfast by setting
``COLLECTFAST_ENABLED = False`` in your settings file. This is useful
when using a local file storage backend for development.


Setup Dedicated Cache Backend
-----------------------------

It's recommended to setup a dedicated cache backend for Collectfast.
Every time Collectfast does not find a lookup for a file in the cache it
will trigger a lookup to the storage backend, so it's recommended to
have a fairly high ``TIMEOUT`` setting.

Set up your dedicated cache in settings.py with the
``COLLECTFAST_CACHE`` setting:

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

**Note:** Collectfast will never clean the cache of obsolete files. To
clean out the entire cache, use ``cache.clear()``. `Read more about
Django's cache
framework. <https://docs.djangoproject.com/en/stable/topics/cache/>`_

**Note:** We recommend you to set the ``MAX_ENTRIES`` setting if you
have more than 300 static files, see 
`#47 <https://github.com/jazzband/collectfast/issues/47>`_


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

Please feel free to contribute by using issues and pull requests.
Discussion is open and welcome.

**Testing**

To run integration tests you need to setup an S3 bucket with the name
``collectfast`` and set your AWS credentials as environment variables. You can
do this by adding them to a file ``aws-credentials`` like this:

.. code:: bash

    export AWS_ACCESS_KEY_ID="XXXX"
    export AWS_SECRET_ACCESS_KEY="XXXX"

And then running the tests with ``. aws-credentials && python runtests.py``.

If you don't feel like setting up an S3 bucket, just skip setting the
environment variables. The integration tests will still run but fail.

To run tests with tox, setup a virtualenv and install tox with
``pip install tox`` then run ``tox`` in the project directory. To only run
tests for a certain environment run e.g. ``tox -e py35-django110``.


License
-------

Collectfast is licensed under the MIT License, see LICENSE file for more
information. Previous versions of Collectfast was licensed under Creative
Commons Attribution-ShareAlike 3.0 Unported License.


.. |Build Status| image:: https://api.travis-ci.org/jazzband/collectfast.svg?branch=master
   :target: https://travis-ci.org/jazzband/collectfast
.. |Windows Build Status| image:: https://ci.appveyor.com/api/projects/status/github/antonagestam/collectfast?branch=master&svg=true
   :target: https://ci.appveyor.com/project/antonagestam/collectfast/
.. |Coverage Status| image:: https://coveralls.io/repos/jazzband/collectfast/badge.png
   :target: https://coveralls.io/r/jazzband/collectfast
.. |Jazzband| image:: https://jazzband.co/static/img/badge.svg
   :target: https://jazzband.co/
