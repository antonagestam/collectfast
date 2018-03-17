from __future__ import with_statement, unicode_literals
from multiprocessing.dummy import Pool
import warnings

from django.contrib.staticfiles.management.commands import collectstatic
from django.utils.encoding import smart_str

from collectfast.etag import should_copy_file
from collectfast.boto import reset_connection, is_boto
from collectfast import settings


class Command(collectstatic.Command):
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--ignore-etag',
            action='store_true',
            dest='ignore_etag',
            default=False,
            help="Deprecated since 0.5.0, use --disable-collectfast instead.")
        parser.add_argument(
            '--disable-collectfast',
            action='store_true',
            dest='disable_collectfast',
            default=False,
            help="Disable Collectfast.")

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.num_copied_files = 0
        self.tasks = []
        self.etags = {}
        self.collectfast_enabled = settings.enabled

        if is_boto(self.storage) and self.storage.preload_metadata is not True:
            self.storage.preload_metadata = True
            warnings.warn(
                "Collectfast does not work properly without "
                "`preload_metadata` set to `True` on the storage class. Try "
                "setting `AWS_PRELOAD_METADATA` to `True`. Overriding "
                "`storage.preload_metadata` and continuing.")

    def set_options(self, **options):
        """
        Set options and handle deprecation.
        """
        ignore_etag = options.pop('ignore_etag', False)
        disable = options.pop('disable_collectfast', False)
        if ignore_etag:
            warnings.warn(
                "--ignore-etag is deprecated since 0.5.0, use "
                "--disable-collectfast instead.")
        if ignore_etag or disable:
            self.collectfast_enabled = False
        super(Command, self).set_options(**options)

    def collect(self):
        """
        Override collect to copy files concurrently. The tasks are populated by
        Command.copy_file() which is called by super().collect().
        """
        ret = super(Command, self).collect()
        if settings.threads:
            Pool(settings.threads).map(self.do_copy_file, self.tasks)
        return ret

    def handle(self, **options):
        """
        Override handle to supress summary output
        """
        super(Command, self).handle(**options)
        return "{} static file{} copied.".format(
            self.num_copied_files,
            '' if self.num_copied_files == 1 else 's')

    def do_copy_file(self, args):
        """
        Determine if file should be copied or not and handle exceptions.
        """
        path, prefixed_path, source_storage = args

        reset_connection(self.storage)

        if self.collectfast_enabled and not self.dry_run:
            try:
                if not should_copy_file(
                        self.storage, path, prefixed_path, source_storage):
                    return False
            except Exception as e:
                if settings.debug:
                    raise
                # Ignore errors and let default collectstatic handle copy
                self.stdout.write(smart_str(
                    "Ignored error in Collectfast:\n%s\n--> Continuing using "
                    "default collectstatic." % e))

        self.num_copied_files += 1
        return super(Command, self).copy_file(
            path, prefixed_path, source_storage)

    def copy_file(self, path, prefixed_path, source_storage):
        """
        Appends path to task queue if threads are enabled, otherwise copies
        the file with a blocking call.
        """
        args = (path, prefixed_path, source_storage)
        if settings.threads:
            self.tasks.append(args)
        else:
            self.do_copy_file(args)

    def delete_file(self, path, prefixed_path, source_storage):
        """
        Override delete_file to skip modified time and exists lookups.
        """
        if not self.collectfast_enabled:
            return super(Command, self).delete_file(
                path, prefixed_path, source_storage)
        if not self.dry_run:
            self.log("Deleting '%s'" % path)
            self.storage.delete(prefixed_path)
        else:
            self.log("Pretending to delete '%s'" % path)
        return True
