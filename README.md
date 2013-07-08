Collectfast
===========

The fast `collectstatic` for Django-apps with S3 as storage backend.

Custom management command that compares the MD5 sum and etag from S3 and if the
two are the same skips file copy. This makes running collect static MUCH faster
if you are using git as a source control system which updates timestamps.

Installation
------------

Install the app using pip:

    pip install Collectfast==0.1.9

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
by using the `--ignore-etag` option.

Cred
----

Original idea taken from [djangosnippets](http://djangosnippets.org/snippets/2889/)

<a rel="license" href="http://creativecommons.org/licenses/by-sa/3.0/"><img alt="Creative Commons License" style="border-width:0" src="http://i.creativecommons.org/l/by-sa/3.0/88x31.png" /></a>
<br />
<span xmlns:dct="http://purl.org/dc/terms/" property="dct:title">
<a xmlns:dct="http://purl.org/dc/terms/" href="https://github.com/FundedByMe/collectfast/" rel="dct:source">
Collectfast
</a>
</span>
by <a xmlns:cc="http://creativecommons.org/ns#" href="http://www.fundedbyme.com/" property="cc:attributionName" rel="cc:attributionURL">FundedByMe</a> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/3.0/">Creative Commons Attribution-ShareAlike 3.0 Unported License</a>.
