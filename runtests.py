#!/usr/bin/env python

import os
import sys
import shutil
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

    # create static dir
    staticfiles_dir = "./static/"
    staticroot_dir = "./static_root/"
    if not os.path.exists(staticfiles_dir):
        os.makedirs(staticfiles_dir)
    if not os.path.exists(staticroot_dir):
        os.makedirs(staticroot_dir)

    settings.configure(**{
        # Set USE_TZ to True to work around bug in django-storages
        "USE_TZ": True,
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
            "django.contrib.staticfiles",
        ),
        "STATIC_URL": "/staticfiles/",
        "STATIC_ROOT": staticroot_dir,
        "STATICFILES_DIRS": [staticfiles_dir],
        "STATICFILES_STORAGE": "storages.backends.s3boto3.S3Boto3Storage",
        "MIDDLEWARE_CLASSES": [],
        "AWS_PRELOAD_METADATA": True,
        "AWS_STORAGE_BUCKET_NAME": "collectfast",
    })

    if options.TEST_SUITE is not None:
        test_arg = "%s.%s" % (app_name, options.TEST_SUITE)
    else:
        test_arg = app_name
    django.setup()

    call_command("test", test_arg)

    # delete static dir
    shutil.rmtree(staticfiles_dir)
    shutil.rmtree(staticroot_dir)

if __name__ == "__main__":
    main()
