Collectfast – A Faster Collectstatic
====================================

[![Downloads](https://pypip.in/v/Collectfast/badge.png)](https://pypi.python.org/pypi/Collectfast)
[![Build Status](https://travis-ci.org/antonagestam/collectfast.svg)](https://travis-ci.org/antonagestam/collectfast)
[![Coverage Status](https://coveralls.io/repos/antonagestam/collectfast/badge.png)](https://coveralls.io/r/antonagestam/collectfast)
[![Join the chat at https://gitter.im/antonagestam/collectfast](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/antonagestam/collectfast?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

The fast `collectstatic` for Django projects with S3 as storage backend.

Running Django's `collectstatic` command can become really slow as more and more files are 
added to a project, especially if heavy libraries such as jQuery UI are included in the source.
This is a custom management command that compares the md5 sum of files with S3 and completely
ignores `modified_time`. The results of the hash lookups are cached locally using your default
Django cache. This can make deploying much faster!


Installation
------------

Install the app using pip:

    $ pip install Collectfast

Make sure you have this in your settings file and add `'collectfast'` to your `INSTALLED_APPS`:

```python
STATICFILES_STORAGE = "storages.backends.s3boto.S3BotoStorage"
AWS_PRELOAD_METADATA = True
INSTALLED_APPS = (
    # …
    'collectfast',
)
```
For Django 1.7+, `'collectfast'` should come before `'django.contrib.staticfiles'`. For Django versions
below 1.7, it should come after `'django.contrib.staticfiles'`. Please note, that failure to do so
will cause Django to use `django.contrib.staticfiles`'s `collectstatic`.

_**Note:** `preload_metadata` of the storage class will be overwritten even if `AWS_PRELOAD_METADATA`
is not set to True see [#30](https://github.com/antonagestam/collectfast/issues/30)_


Setup Dedicated Cache Backend
-----------------------------

It's recommended to setup a dedicated cache backend for Collectfast. Every time Collectfast does not
find a lookup for a file in the cache it will trigger a lookup to the storage backend, so it's
recommended to have a fairly high `TIMEOUT` setting.

Set up your dedicated cache in settings.py with the `COLLECTFAST_CACHE` setting:

```python
CACHES = {
    'default': {
        # Your default cache
    },
    'collectfast': {
        # Your dedicated Collectfast cache
    }
}

COLLECTFAST_CACHE = 'collectfast'
```

By default Collectfast will use the `default` cache.

_**Note:** Collectfast will never clean the cache of obsolete files. To clean out the entire
cache, use `cache.clear()`.
[Read more about Django's cache framework.](https://docs.djangoproject.com/en/stable/topics/cache/)_


Usage
-----

Collectfast overrides Django's builtin `collectstatic` command so just run
`python manage.py collectstatic` as normal. You can disable collectfast
by using the `--ignore-etag` option.

You can also disable collectfast by setting `COLLECTFAST_ENABLED = False` in
your settings file. This is useful when using a local file storage backend
for development.


Contribution
------------

Please feel free to contribute by using issues and pull requests. Discussion is open and welcome.
Testing is currently being implemented and will be mandatory for new features once merged.


License
-------

<a rel="license" href="http://creativecommons.org/licenses/by-sa/3.0/"><img alt="Creative Commons License" style="border-width:0" src="http://i.creativecommons.org/l/by-sa/3.0/88x31.png" /></a>

<span xmlns:dct="http://purl.org/dc/terms/" property="dct:title">
<a xmlns:dct="http://purl.org/dc/terms/" href="https://github.com/FundedByMe/collectfast/" rel="dct:source">
Collectfast
</a>
</span>
is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/3.0/">Creative Commons Attribution-ShareAlike 3.0 Unported License</a>.

Original idea taken from [this snippet.](http://djangosnippets.org/snippets/2889/)
