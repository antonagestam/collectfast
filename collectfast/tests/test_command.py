"""
To test:

* Command.collect
    - Sets collect_time properly
    - Calls and returns value of super
* Command.get_cache_key
    - test return value (needs both 2.7 and 3.x)
* Command.get_lookup
    - Uses self.lookups if populated
    - Uses cache if populated
    - Properly calls storage.bucket.lookup
    - Properly populates cache and self.lookups
* Command.destroy_lookup
    - Properly deletes value from cache and self.lookups
* Command.copy_file
    - Respects self.ignore_etag and self.dry_run
    - Respects storage.location
    - Produces a proper md5 checksum
    - Returns False and increments self.num_skipped_files if matching checksums
    - Invalidates cache and self.lookups
    - Properly calls super
"""

import sys
from StringIO import StringIO
from contextlib import contextmanager
from unittest import TestCase
from django.core.management import call_command

from ..management.commands.collectstatic import Command


@contextmanager
def redirect_output(out=sys.stdout, err=sys.stderr):
    """
    Redirect stdout to variable, see http://stackoverflow.com/questions/13250050/redirecting-the-output-of-a-python-function-from-stdout-to-variable-in-python
    """
    saved = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved


class TestCommand(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        with redirect_output(out, err):
            out.flush()
            err.flush()
            call_command('collectstatic', interactive=False, *args, **kwargs)
            output = out.getvalue()
        return output

    def get_command(self, *args, **kwargs):
        return Command(*args, **kwargs)

    def test_collect(self):
        command = self.get_command()
        command.collect()
        self.assertEqual(command.num_skipped_files, 0)
        self.assertIsInstance(command.collect_time, str)

    def test_get_cache_key(self):
        pass

    def test_get_lookup(self):
        pass

    def test_destroy_lookup(self):
        pass

    def test_copy_file(self):
        pass