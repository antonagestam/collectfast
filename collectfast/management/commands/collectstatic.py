from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

from django.conf import settings as django_settings
from django.contrib.staticfiles.management.commands import collectstatic
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.core.management.base import CommandParser

from collectfast import __version__
from collectfast import settings
from collectfast.strategies import DisabledStrategy
from collectfast.strategies import load_strategy
from collectfast.strategies import Strategy


Task = Tuple[str, str, Storage]


class Command(collectstatic.Command):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.num_copied_files = 0
        self.tasks: List[Task] = []
        self.collectfast_enabled = settings.enabled
        self.strategy: Strategy = DisabledStrategy(Storage())
        self.found_files: Dict[str, Tuple[Storage, str]] = {}

    @staticmethod
    def _load_strategy() -> Type[Strategy[Storage]]:
        strategy_str = getattr(django_settings, "COLLECTFAST_STRATEGY", None)
        if strategy_str is not None:
            return load_strategy(strategy_str)

        raise ImproperlyConfigured(
            "No strategy configured, please make sure COLLECTFAST_STRATEGY is set."
        )

    def get_version(self) -> str:
        return __version__

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--disable-collectfast",
            action="store_true",
            dest="disable_collectfast",
            default=False,
            help="Disable Collectfast.",
        )

    def set_options(self, **options: Any) -> None:
        self.collectfast_enabled = self.collectfast_enabled and not options.pop(
            "disable_collectfast"
        )
        if self.collectfast_enabled:
            self.strategy = self._load_strategy()(self.storage)
        super().set_options(**options)

    def collect(self) -> Dict[str, List[str]]:
        """
        Override collect to copy files concurrently. The tasks are populated by
        Command.copy_file() which is called by super().collect().
        """
        if not self.collectfast_enabled or not settings.threads:
            return super().collect()

        # Store original value of post_process in super_post_process and always
        # set the value to False to prevent the default behavior from
        # interfering when using threads. See maybe_post_process().
        super_post_process = self.post_process
        self.post_process = False

        return_value = super().collect()

        with ThreadPoolExecutor(settings.threads) as pool:
            pool.map(self.maybe_copy_file, self.tasks)

        self.maybe_post_process(super_post_process)
        return_value["post_processed"] = self.post_processed_files

        return return_value

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        """Override handle to suppress summary output."""
        ret = super().handle(**options)
        if not self.collectfast_enabled:
            return ret
        plural = "" if self.num_copied_files == 1 else "s"
        return f"{self.num_copied_files} static file{plural} copied."

    def maybe_copy_file(self, args: Task) -> None:
        """Determine if file should be copied or not and handle exceptions."""
        path, prefixed_path, source_storage = args

        # Build up found_files to look identical to how it's created in the
        # builtin command's collect() method so that we can run post_process
        # after all parallel uploads finish.
        self.found_files[prefixed_path] = (source_storage, path)

        if self.collectfast_enabled and not self.dry_run:
            self.strategy.pre_should_copy_hook()

            if not self.strategy.should_copy_file(path, prefixed_path, source_storage):
                self.log(f"Skipping '{path}'")
                self.strategy.on_skip_hook(path, prefixed_path, source_storage)
                return

        self.num_copied_files += 1

        existed = prefixed_path in self.copied_files
        super().copy_file(path, prefixed_path, source_storage)
        copied = not existed and prefixed_path in self.copied_files
        if copied:
            self.strategy.post_copy_hook(path, prefixed_path, source_storage)
        else:
            self.strategy.on_skip_hook(path, prefixed_path, source_storage)

    def copy_file(self, path: str, prefixed_path: str, source_storage: Storage) -> None:
        """
        Append path to task queue if threads are enabled, otherwise copy the
        file with a blocking call.
        """
        args = (path, prefixed_path, source_storage)
        if settings.threads and self.collectfast_enabled:
            self.tasks.append(args)
        else:
            self.maybe_copy_file(args)

    def delete_file(
        self, path: str, prefixed_path: str, source_storage: Storage
    ) -> bool:
        """Override delete_file to skip modified time and exists lookups."""
        if not self.collectfast_enabled:
            return super().delete_file(path, prefixed_path, source_storage)

        if self.dry_run:
            self.log(f"Pretending to delete '{path}'")
            return True

        self.log(f"Deleting '{path}' on remote storage")

        try:
            self.storage.delete(prefixed_path)
        except self.strategy.delete_not_found_exception:
            pass

        return True

    def maybe_post_process(self, super_post_process: bool) -> None:
        # This method is extracted and modified from the collect() method of the
        # builtin collectstatic command.
        # https://github.com/django/django/blob/5320ba98f3d253afcaa76b4b388a8982f87d4f1a/django/contrib/staticfiles/management/commands/collectstatic.py#L124

        if not super_post_process or not hasattr(self.storage, "post_process"):
            return

        processor = self.storage.post_process(self.found_files, dry_run=self.dry_run)

        for original_path, processed_path, processed in processor:
            if isinstance(processed, Exception):
                self.stderr.write("Post-processing '%s' failed!" % original_path)
                # Add a blank line before the traceback, otherwise it's
                # too easy to miss the relevant part of the error message.
                self.stderr.write("")
                raise processed
            if processed:
                self.log(
                    "Post-processed '%s' as '%s'" % (original_path, processed_path),
                    level=2,
                )
                self.post_processed_files.append(original_path)
            else:
                self.log("Skipped post-processing '%s'" % original_path)
