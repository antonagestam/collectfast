from __future__ import with_statement
import hashlib
from optparse import make_option

from django.contrib.staticfiles.management.commands import collectstatic

class Command(collectstatic.Command):
    option_list = collectstatic.Command.option_list + (
        make_option('--ignore_etag',
            action="store_true", dest="ignore_etag", default=False,
            help="Upload the file even though the ETags match."),
    )

    def set_options(self, **options):
        self.ignore_etag = options.pop('ignore_etag', False)
        super(Command, self).set_options(**options)

    def copy_file(self, path, prefixed_path, source_storage):
        """
        Attempt to generate an md5 hash of the local file and compare it with
        the S3 version's ETag before copying the file.

        """

        if not self.ignore_etag:
            try:
                # Get ETag from storage
                storage_etag = self.storage.bucket.lookup(prefixed_path).etag

                # Create md5 checksum from local file
                file_contents = source_storage.open(path).read()
                local_etag = '"%s"' % hashlib.md5(file_contents).hexdigest()

                # Compare checksums and skip copying if matching
                if storage_etag == local_etag:
                    self.log(u"Skipping '%s'" % path, level=1)
                    return False
            except:
                # Ignore errors, let default Command handle it
                pass

        return super(Command, self).copy_file(path, prefixed_path,
                                              source_storage)