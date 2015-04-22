#!/usr/bin/env python

import os
import sys

from optparse import OptionParser

import django
from django.conf import settings
from django.core.management import call_command


def main():
    parser = OptionParser()
    parser.add_option("--DATABASE_ENGINE", dest="DATABASE_ENGINE", default="sqlite3")
    parser.add_option("--DATABASE_NAME", dest="DATABASE_NAME", default="")
    parser.add_option("--DATABASE_USER", dest="DATABASE_USER", default="")
    parser.add_option("--DATABASE_PASSWORD", dest="DATABASE_PASSWORD", default="")
    parser.add_option("--TEST", dest="TEST_SUITE", default=None)

    options, args = parser.parse_args()

    # check for app in args
    app_path = 'collectfast'
    parent_dir, app_name = os.path.split(app_path)
    sys.path.insert(0, parent_dir)

    settings.configure(**{
        "DATABASES": {
            'default': {
                "ENGINE": 'django.db.backends.%s' % options.DATABASE_ENGINE,
                "NAME": options.DATABASE_NAME,
                "USER": options.DATABASE_USER,
                "PASSWORD": options.DATABASE_PASSWORD,
            }
        },
        "CACHES": {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'test-collectfast'
            }
        },
        "ROOT_URLCONF": app_name + ".urls",
        "TEMPLATE_LOADERS": (
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
            "django.template.loaders.eggs.Loader",
        ),
        "TEMPLATE_DIRS": (
            os.path.join(os.path.dirname(__file__),
                         "collectfast/templates"),
        ),
        "INSTALLED_APPS": (
            "django.contrib.auth",
            "django.contrib.contenttypes",
            app_name,
        ),
        "STATIC_URL": "/staticfiles/",
        "STATIC_ROOT": "./",

        "AWS_PRELOAD_METADATA": True,
        "MIDDLEWARE_CLASSES": [],
    })

    if options.TEST_SUITE is not None:
        test_arg = "%s.%s" % (app_name, options.TEST_SUITE)
    else:
        test_arg = app_name
    if django.VERSION >= (1, 7):
        django.setup()

    call_command("test", test_arg)

if __name__ == "__main__":
    main()
