from __future__ import with_statement, unicode_literals
from multiprocessing.dummy import Pool
import warnings

from django.contrib.staticfiles.management.commands import collectstatic
from django.utils.encoding import smart_str

from collectfast.etag import should_copy_file
from collectfast import settings
from collectfast.storage_extensions import get_storage_extensions


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

    @property
    def storage_extensions(self):
        if not hasattr(self, '_storage_extensions'):
            self._storage_extensions = get_storage_extensions(self.storage)
        return self._storage_extensions

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

        self.storage_extensions.reset_connection()
        source_storage_extensions= get_storage_extensions(source_storage)

        if self.collectfast_enabled and not self.dry_run:
            try:
                if not should_copy_file(
                        self.storage_extensions, path, prefixed_path, source_storage_extensions):
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
            self.storage_extensions.try_delete(prefixed_path)
        else:
            self.log("Pretending to delete '%s'" % path)
        return True
