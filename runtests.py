#!/usr/bin/env python
import os
import shutil
import sys
from optparse import OptionParser

import django
from django.conf import settings
from django.core.management import call_command

from collectfast.tests import settings as test_settings


def configure_django():
    # type: () -> None
    settings.configure(**vars(test_settings))
    django.setup()


def main():
    # type: () -> None
    configure_django()

    parser = OptionParser()
    parser.add_option("--target", dest="target", default=None)
    parser.add_option(
        "--skip-cleanup", dest="skip_cleanup", default=False, action="store_true"
    )

    options, args = parser.parse_args()

    app_path = "collectfast"
    parent_dir, app_name = os.path.split(app_path)
    sys.path.insert(0, parent_dir)

    # create static dir
    staticfiles_dir = test_settings.STATICFILES_DIRS[0]
    staticroot_dir = test_settings.STATIC_ROOT
    if not os.path.exists(staticfiles_dir):
        os.makedirs(staticfiles_dir)
    if not os.path.exists(staticroot_dir):
        os.makedirs(staticroot_dir)

    if options.target is not None:
        test_arg = "%s.%s" % (app_name, options.target)
    else:
        test_arg = app_name

    try:
        call_command("test", test_arg)
    finally:
        if options.skip_cleanup:
            return
        # delete static dirs
        shutil.rmtree(staticfiles_dir)
        shutil.rmtree(staticroot_dir)


if __name__ == "__main__":
    main()
