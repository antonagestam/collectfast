Collectfast
===========

[![Downloads](https://pypip.in/v/Collectfast/badge.png)](https://pypi.python.org/pypi/Collectfast)

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
