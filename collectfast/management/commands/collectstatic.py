# -*- coding: utf-8 -*-

from __future__ import with_statement
from optparse import make_option
import hashlib
import datetime

from django.conf import settings
from django.contrib.staticfiles.management.commands import collectstatic
from django.core.cache import get_cache
from django.core.files.storage import FileSystemStorage
from django.core.management.base import CommandError
from django.utils.encoding import smart_str

try:
    from django.utils.six.moves import input as _input
except ImportError:
    _input = raw_input

cache = get_cache(getattr(settings, "COLLECTFAST_CACHE", "default"))


class Command(collectstatic.Command):
    option_list = collectstatic.Command.option_list + (
        make_option('--ignore-etag',
            action="store_true", dest="ignore_etag", default=False,
            help="Upload the file even though the ETags match."),
    )

    lookups = None
    cache_key_prefix = 'collectfast_asset_'

    def set_options(self, **options):
        self.ignore_etag = options.pop('ignore_etag', False)
        super(Command, self).set_options(**options)

    def collect(self):
        """Override collect method to track time"""

        self.num_skipped_files = 0
        start = datetime.datetime.now()
        ret = super(Command, self).collect()
        self.collect_time = str(datetime.datetime.now() - start)
        return ret

    def get_cache_key(self, path):
        # Python 2/3 support for path hashing
        try:
            path_hash = hashlib.md5(path).hexdigest()
        except TypeError:
            path_hash = hashlib.md5(path.encode('utf-8')).hexdigest()
        return self.cache_key_prefix + path_hash

    def get_storage_lookup(self, path):
        return self.storage.bucket.lookup(path)

    def get_lookup(self, path):
        """Get lookup from local dict, cache or S3 — in that order"""

        if self.lookups is None:
            self.lookups = {}

        if path not in self.lookups:
            cache_key = self.get_cache_key(path)
            cached = cache.get(cache_key, False)

            if cached is False:
                self.lookups[path] = self.get_storage_lookup(path)
                cache.set(cache_key, self.lookups[path])
            else:
                self.lookups[path] = cached

        return self.lookups[path]

    def destroy_lookup(self, path):
        if self.lookups is not None and path in self.lookups:
            del self.lookups[path]
        cache.delete(self.get_cache_key(path))

    def get_file_hash(self, storage, path):
        contents = storage.open(path).read()
        file_hash = '"%s"' % hashlib.md5(contents).hexdigest()
        return file_hash

    def copy_file(self, path, prefixed_path, source_storage):
        """
        Attempt to generate an md5 hash of the local file and compare it with
        the S3 version's hash before copying the file.

        """

        normalized_path = self.storage._normalize_name(prefixed_path)

        if not self.ignore_etag and not self.dry_run:
            try:
                storage_lookup = self.get_lookup(normalized_path)
                local_etag = self.get_file_hash(source_storage, path)

                # Compare checksums and skip copying if matching
                if storage_lookup.etag == local_etag:
                    self.log(u"Skipping '%s' based on matching ETags" % path,
                             level=2)
                    self.num_skipped_files += 1
                    return False
                else:
                    self.log(u"ETag didn't match", level=2)
            except:
                # Ignore errors, let default Command handle it
                pass

            # Invalidate cached versions of lookup if copy is done
            self.destroy_lookup(normalized_path)

        return super(Command, self).copy_file(
            path, prefixed_path, source_storage)

    def delete_file(self, path, prefixed_path, source_storage):
        """Override delete_file to skip modified time and exists lookups"""
        if self.dry_run:
            self.log(u"Pretending to delete '%s'" % path)
        else:
            self.log(u"Deleting '%s'" % path)
            self.storage.delete(prefixed_path)
        return True

    def handle_noargs(self, **options):
        self.set_options(**options)
        # Warn before doing anything more.
        if (isinstance(self.storage, FileSystemStorage) and
                self.storage.location):
            destination_path = self.storage.location
            destination_display = ':\n\n    %s' % destination_path
        else:
            destination_path = None
            destination_display = '.'

        if self.clear:
            clear_display = 'This will DELETE EXISTING FILES!'
        else:
            clear_display = 'This will overwrite existing files!'

        if self.interactive:
            confirm = _input(u"""
You have requested to collect static files at the destination
location as specified in your settings%s

%s
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """
% (destination_display, clear_display))
            if confirm != 'yes':
                raise CommandError("Collecting static files cancelled.")

        collected = self.collect()
        modified_count = len(collected['modified'])
        unmodified_count = len(collected['unmodified'])
        post_processed_count = len(collected['post_processed'])

        if self.verbosity >= 1:
            template = ("Collected static files in %(collect_time)s."
                        "\nSkipped %(num_skipped)i already synced files."
                        "\n%(modified_count)s %(identifier)s %(action)s"
                        "%(destination)s%(unmodified)s%(post_processed)s.\n")
            summary = template % {
                'modified_count': modified_count,
                'identifier': 'static file' + (modified_count != 1 and 's' or ''),
                'action': self.symlink and 'symlinked' or 'copied',
                'destination': (destination_path and " to '%s'"
                                % destination_path or ''),
                'unmodified': (collected['unmodified'] and ', %s unmodified'
                               % unmodified_count or ''),
                'post_processed': (collected['post_processed'] and
                                   ', %s post-processed'
                                   % post_processed_count or ''),
                'num_skipped': self.num_skipped_files,
                'collect_time': self.collect_time,
            }
            self.stdout.write(smart_str(summary))
