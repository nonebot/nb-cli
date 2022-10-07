import os
import signal
import platform
import threading
from pathlib import Path
from types import FrameType
from typing import List, Iterator, Optional

import click
from watchfiles import watch

from nb_cli.config import LocalConfig

from .process import NoneBotProcess

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class FileFilter:
    def __init__(self, config: LocalConfig):
        default_includes = ["*.py"]
        self.includes = [
            default
            for default in default_includes
            if default not in config.get("reload_excludes")
        ]
        self.includes.extend(config.get("reload_includes"))
        self.includes = list(set(self.includes))

        default_excludes = [".*", "~*"]
        self.excludes = [
            default
            for default in default_excludes
            if default not in config.get("reload_includes")
        ]
        self.exclude_dirs = []
        for e in config.get("reload_excludes"):
            p = Path(e)
            try:
                is_dir = p.is_dir()
            except OSError:  # pragma: no cover
                # gets raised on Windows for values like "*.py"
                is_dir = False

            if is_dir:
                self.exclude_dirs.append(p)
            else:
                self.excludes.append(e)
        self.excludes = list(set(self.excludes))

    def __call__(self, path: Path) -> bool:
        for include_pattern in self.includes:
            if path.match(include_pattern):
                for exclude_dir in self.exclude_dirs:
                    if exclude_dir in path.parents:
                        return False

                for exclude_pattern in self.excludes:
                    if path.match(exclude_pattern):
                        return False

                return True
        return False


class WatchFilesReload:
    def __init__(self, config: LocalConfig, app: NoneBotProcess):
        self.pid = os.getpid()
        self.app = app
        self.reload_dirs = []
        self.should_exit = threading.Event()
        self.is_restarting = False
        for directory in config.get("reload_dirs"):
            if Path.cwd() not in Path(directory).parents:
                self.reload_dirs.append(directory)
        if Path.cwd() not in self.reload_dirs:
            self.reload_dirs.append(Path.cwd())

        self.watch_filter = FileFilter(config)
        self.watcher = watch(
            *self.reload_dirs,
            watch_filter=None,
            stop_event=self.should_exit,
            # using yield_on_timeout here mostly to make sure tests don't
            # hang forever, won't affect the class's behavior
            yield_on_timeout=True,
        )

    def __iter__(self) -> Iterator[Optional[List[Path]]]:
        return self

    def __next__(self) -> Optional[List[Path]]:
        return self.should_restart()

    def startup(self) -> None:
        message = f"Started reloader process [{self.pid}] using WatchFiles"
        click.echo(message)

        for sig in HANDLED_SIGNALS:
            signal.signal(sig, self.signal_handler)

        self.app.run()

    def run(self) -> None:
        self.startup()
        for changes in self:
            if changes:
                click.echo(
                    "WatchFiles detected changes in %s. Reloading..."
                    ", ".join(map(_display_path, changes)),
                )
                self.restart()

        self.shutdown()

    def restart(self) -> None:
        self.is_restarting = True
        self.app.terminate()
        self.app.run()

    def shutdown(self) -> None:
        message = "Stopping reloader process [{}]".format(str(self.pid))
        click.echo(message)

    def should_restart(self) -> Optional[List[Path]]:
        changes = next(self.watcher)
        if changes:
            unique_paths = {Path(c[1]) for c in changes}
            return [p for p in unique_paths if self.watch_filter(p)]
        return None

    def signal_handler(self, sig: int, frame: Optional[FrameType]) -> None:
        if platform.system() == "Windows" and self.is_restarting:
            self.is_restarting = False
        else:
            self.should_exit.set()


def _display_path(path: Path) -> str:
    try:
        return f"'{path.relative_to(Path.cwd())}'"
    except ValueError:
        return f"'{path}'"
