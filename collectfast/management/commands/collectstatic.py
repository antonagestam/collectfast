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
        """Set options and handle deprecation."""
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
        ret = super().collect()
        if not self.collectfast_enabled:
            return ret
        if settings.threads:
            with ThreadPoolExecutor(settings.threads) as pool:
                pool.map(self.maybe_copy_file, self.tasks)
        return ret

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

        if self.collectfast_enabled and not self.dry_run:
            self.strategy.pre_should_copy_hook()

            if not self.strategy.should_copy_file(path, prefixed_path, source_storage):
                self.log(f"Skipping '{path}'")
                return

        self.num_copied_files += 1
        return super().copy_file(path, prefixed_path, source_storage)

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
