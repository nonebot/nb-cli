import asyncio
import logging
from pathlib import Path
from typing import Any, List, Callable, Optional, Coroutine

from watchfiles import awatch

from nb_cli import _

from .signal import remove_signal_handler, register_signal_handler


class FileFilter:
    def __init__(
        self, includes: Optional[List[str]] = None, excludes: Optional[List[str]] = None
    ):
        includes = includes or []
        excludes = excludes or []

        default_includes = ["*.py", "pyproject.toml"]
        self.includes = [
            default for default in default_includes if default not in excludes
        ]
        self.includes.extend(includes)
        self.includes = list(set(self.includes))

        default_excludes = [".*", ".py[cod]", ".sw.*", "~*"]
        self.excludes = [
            default for default in default_excludes if default not in includes
        ]
        self.exclude_dirs = []
        for e in excludes:
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


class Reloader:
    def __init__(
        self,
        startup_func: Callable[[], Coroutine[Any, Any, asyncio.subprocess.Process]],
        shutdown_func: Callable[
            [asyncio.subprocess.Process], Coroutine[Any, Any, None]
        ],
        *,
        reload_dirs: Optional[List[Path]] = None,
        file_filter: Optional[FileFilter] = None,
        reload_delay: float = 0.5,
        cwd: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.startup_func = startup_func
        self.shutdown_func = shutdown_func
        self.process: Optional[asyncio.subprocess.Process] = None

        self.cwd = (cwd or Path.cwd()).resolve()
        self.logger = logger

        self.reload_dirs: List[Path] = []
        for directory in reload_dirs or []:
            directory = directory.resolve()
            if self.cwd not in directory.parents:
                self.reload_dirs.append(directory)
        if self.cwd not in self.reload_dirs:
            self.reload_dirs.append(self.cwd)

        self.watch_filter = file_filter or FileFilter()
        self.reload_delay = reload_delay

        self.should_exit = asyncio.Event()
        self.watcher = awatch(
            *self.reload_dirs,
            watch_filter=None,
            stop_event=self.should_exit,
            # using yield_on_timeout here mostly to make sure tests don't
            # hang forever, won't affect the class's behavior
            yield_on_timeout=True,
        )

    async def __aenter__(self):
        await self.startup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.shutdown()

    def __aiter__(self):
        return self

    async def __anext__(self) -> Optional[List[Path]]:
        return await self.should_restart()

    async def run(self) -> None:
        async with self:
            async for changes in self:
                if self.process and self.process.returncode is not None:
                    break
                if changes:
                    if self.logger:
                        self.logger.info(
                            _(
                                "Watchfiles detected changes in {paths}. Reloading..."
                            ).format(paths=", ".join(map(self._display_path, changes)))
                        )
                    await self.restart()

    async def startup(self) -> None:
        register_signal_handler(self.handle_exit)

        self.process = await self.startup_func()
        if self.logger:
            self.logger.info(
                _("Started reloader with process [{pid}].").format(pid=self.process.pid)
            )

    async def restart(self) -> None:
        if self.process and self.process.returncode is None:
            await self.shutdown_func(self.process)

        await asyncio.sleep(self.reload_delay)

        self.process = await self.startup_func()
        if self.logger:
            self.logger.info(
                _("Restarted process [{pid}].").format(pid=self.process.pid)
            )

    async def shutdown(self) -> None:
        remove_signal_handler(self.handle_exit)

        if self.process and self.process.returncode is None:
            if self.logger:
                self.logger.info(
                    _("Shutting down process [{pid}]...").format(pid=self.process.pid)
                )
            await self.shutdown_func(self.process)

        if self.logger:
            self.logger.info(_("Stopped reloader."))

    async def should_restart(self) -> Optional[List[Path]]:
        changes = await self.watcher.__anext__()
        if changes:
            unique_paths = {Path(c[1]) for c in changes}
            return [p for p in unique_paths if self.watch_filter(p)]
        return None

    def handle_exit(self, sig, frame):
        self.should_exit.set()

    def _display_path(self, path: Path) -> str:
        try:
            return f'"{path.relative_to(self.cwd)}"'
        except ValueError:
            return f'"{path}"'
