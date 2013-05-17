# -*- coding: utf-8 -*-

from __future__ import with_statement
import hashlib
from optparse import make_option
import datetime

from django.contrib.staticfiles.management.commands import collectstatic
from django.core.cache import cache

from dateutil import parser
import pytz

class Command(collectstatic.Command):
    option_list = collectstatic.Command.option_list + (
        make_option('--ignore_etag',
            action="store_true", dest="ignore_etag", default=False,
            help="Upload the file even though the ETags match."),
    )

    lookups = None

    def set_options(self, **options):
        self.ignore_etag = options.pop('ignore_etag', False)
        super(Command, self).set_options(**options)

    def collect(self, *args, **kwargs):
        """Override collect method to track time"""

        start = datetime.datetime.now()
        ret = super(Command, self).collect(*args, **kwargs)
        self.log("Collected static in " + str(datetime.datetime.now() - start),
                 level=1)
        return ret

    def get_cache_key(self, path):
        return 'collectfast_asset_' + hashlib.md5(path).hexdigest()

    def get_lookup(self, path):
        """Get lookup from local dict, cache or S3 — in that order"""

        if self.lookups is None:
            self.lookups = {}

        if path not in self.lookups:
            cache_key = self.get_cache_key(path)
            cached = cache.get(cache_key, False)

            if cached is False:
                self.lookups[path] = self.storage.bucket.lookup(path)
                cache.set(cache_key, self.lookups[path])
            else:
                self.lookups[path] = cached

        return self.lookups[path]

    def destroy_lookup(self, path):
        del self.lookups[path]
        cache.delete(self.get_cache_key(path))

    def get_last_modified(self, path):
        return parser.parse(self.get_lookup(path).last_modified)

    def get_local_modified(self, path, storage):
        date = storage.modified_time(path)
        utc = pytz.UTC
        return utc.localize(date)

    def copy_file(self, path, prefixed_path, source_storage):
        """
        Attempt to generate an md5 hash of the local file and compare it with
        the S3 version's ETag before copying the file.

        """

        if not self.ignore_etag:
            try:
                storage_lookup = self.get_lookup(prefixed_path)
                local_file = source_storage.open(prefixed_path)
                storage_modified = self.get_last_modified(prefixed_path)
                local_modified = self.get_local_modified(prefixed_path,
                                                         source_storage)

                # Compare last_modified dates
                if local_modified > storage_modified:
                    self.log(u"Skipping '%s' due to last_modified" % path,
                             level=1)
                    return False

                # Create md5 checksum from local file
                file_contents = local_file.read()
                local_etag = '"%s"' % hashlib.md5(file_contents).hexdigest()

                # Compare checksums and skip copying if matching
                if storage_lookup.etag == local_etag:
                    self.log(u"Skipping '%s' due to ETag" % path, level=1)
                    return False
            except Exception, e:
                # Ignore errors, let default Command handle it
                raise e
                #pass

            # Invalidate cached versions of lookup if copy is done
            self.destroy_lookup(prefixed_path)

        return super(Command, self).copy_file(path, prefixed_path,
                                              source_storage)