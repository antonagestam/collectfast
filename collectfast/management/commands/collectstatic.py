# -*- coding: utf-8 -*-

from __future__ import with_statement, unicode_literals
import hashlib
import datetime

from django.conf import settings
from django.contrib.staticfiles.management.commands import collectstatic
from django.core.cache import caches
from django.core.files.storage import FileSystemStorage
from django.core.management.base import CommandError
from django.utils.encoding import smart_str


try:
    from django.utils.six.moves import input as _input
except ImportError:
    _input = raw_input  # noqa

collectfast_cache = getattr(settings, "COLLECTFAST_CACHE", "default")
cache = caches[collectfast_cache]
debug = getattr(
    settings, "COLLECTFAST_DEBUG", getattr(settings, "DEBUG", False))


class Command(collectstatic.Command):

    etags = None
    cache_key_prefix = 'collectfast03_asset_'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--ignore-etag',
            action='store_true',
            dest='ignore_etag',
            default=False,
            help="Disable Collectfast.")

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.storage.preload_metadata = True
        if getattr(settings, 'AWS_PRELOAD_METADATA', False) is not True:
            self._pre_setup_log(
                "----> WARNING!\nCollectfast does not work properly without "
                "`AWS_PRELOAD_METADATA` set to `True`.\nOverriding "
                "`storage.preload_metadata` and continuing.")

    def set_options(self, **options):
        self.ignore_etag = options.pop('ignore_etag', False)
        if self.ignore_etag:
            self.collectfast_enabled = False
        else:
            self.collectfast_enabled = getattr(
                settings, "COLLECTFAST_ENABLED", True)
        super(Command, self).set_options(**options)

    def _pre_setup_log(self, message):
        print(message)

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

    def get_boto3_etag(self, path):
        try:
            return self.storage.bucket.Object(path).e_tag
        except:
            return None

    def get_remote_etag(self, path):
        try:
            return self.storage.bucket.get_key(path).etag
        except AttributeError:
            return self.get_boto3_etag(path)

    def get_etag(self, path):
        """Get etag from local dict, cache or S3 — in that order"""

        if self.etags is None:
            self.etags = {}

        if path not in self.etags:
            cache_key = self.get_cache_key(path)
            cached = cache.get(cache_key, False)

            if cached is False:
                self.etags[path] = self.get_remote_etag(path)
                cache.set(cache_key, self.etags[path])
            else:
                self.etags[path] = cached

        return self.etags[path]

    def destroy_etag(self, path):
        if self.etags is not None and path in self.etags:
            del self.etags[path]
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
        if self.collectfast_enabled and not self.dry_run:
            normalized_path = self.storage._normalize_name(
                prefixed_path).replace('\\', '/')
            try:
                storage_etag = self.get_etag(normalized_path)
                local_etag = self.get_file_hash(source_storage, path)

                # Compare hashes and skip copying if matching
                if storage_etag == local_etag:
                    self.log(
                        "Skipping '%s' based on matching file hashes" % path,
                        level=2)
                    self.num_skipped_files += 1
                    return False
                else:
                    self.log("Hashes did not match", level=2)
            except Exception as e:
                if debug:
                    raise
                # Ignore errors and let super Command handle it
                self.stdout.write(smart_str(
                    "Ignored error in Collectfast:\n%s\n--> Continuing using "
                    "default collectstatic." % e))

            # Invalidate cached versions of lookup if copy is done
            self.destroy_etag(normalized_path)

        return super(Command, self).copy_file(
            path, prefixed_path, source_storage)

    def delete_file(self, path, prefixed_path, source_storage):
        """Override delete_file to skip modified time and exists lookups"""
        if not self.collectfast_enabled:
            return super(Command, self).delete_file(
                path, prefixed_path, source_storage)
        if self.dry_run:
            self.log("Pretending to delete '%s'" % path)
        else:
            self.log("Deleting '%s'" % path)
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
            confirm = _input("""
You have requested to collect static files at the destination
location as specified in your settings%s

%s
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """ % (
                destination_display, clear_display))
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
                'identifier': 'static file' + (
                    modified_count != 1 and 's' or ''),
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
