import sys
import asyncio
from pathlib import Path
from typing import IO, Any, List, Callable, Optional, Coroutine, cast

from watchfiles import awatch

from nb_cli.consts import WINDOWS

from .signal import remove_signal_handler, register_signal_handler


class FileFilter:
    def __init__(
        self, includes: Optional[List[str]] = None, excludes: Optional[List[str]] = None
    ):
        includes = includes or []
        excludes = excludes or []

        default_includes = ["*.py"]
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
        reload_dirs: Optional[List[Path]] = None,
        file_filter: Optional[FileFilter] = None,
        cwd: Optional[Path] = None,
        stdout: Optional[IO[Any]] = None,
    ) -> None:
        self.startup_func = startup_func
        self.shutdown_func = shutdown_func
        self.process: Optional[asyncio.subprocess.Process] = None

        self.cwd = cwd or Path.cwd()
        self.stdout = stdout or sys.stdout

        self.reload_dirs = []
        for directory in reload_dirs or []:
            if self.cwd not in directory.parents:
                self.reload_dirs.append(directory)
        if self.cwd not in self.reload_dirs:
            self.reload_dirs.append(self.cwd)

        self.watch_filter = file_filter or FileFilter()
        self.should_exit = asyncio.Event()
        self.is_restarting: bool = False
        self.watcher = awatch(
            *self.reload_dirs,
            watch_filter=None,
            stop_event=self.should_exit,
            # using yield_on_timeout here mostly to make sure tests don't
            # hang forever, won't affect the class's behavior
            yield_on_timeout=True,
        )

    def __aiter__(self):
        return self

    async def __anext__(self) -> Optional[List[Path]]:
        return await self.should_restart()

    async def startup(self) -> None:
        register_signal_handler(self.handle_exit)

        self.process = await self.startup_func()
        print(f"Started reloader with process [{self.process.pid}].", file=self.stdout)

    async def run(self) -> None:
        await self.startup()

        async for changes in self:
            if self.process.returncode is not None:  # type: ignore
                break
            if changes:
                print(
                    "Watchfiles detected changes in "
                    f"{', '.join(map(self._display_path, changes))}. Reloading...",
                    file=self.stdout,
                )
                await self.restart()

        await self.shutdown()

    async def restart(self) -> None:
        self.is_restarting = True
        await self.shutdown_func(cast(asyncio.subprocess.Process, self.process))
        self.process = await self.startup_func()
        print(f"Restarted process [{self.process.pid}].", file=self.stdout)

    async def shutdown(self) -> None:
        remove_signal_handler(self.handle_exit)

        if self.process:
            print(f"Shutting down process [{self.process.pid}]...", file=self.stdout)
            await self.shutdown_func(self.process)
            print("Stopped reloader.", file=self.stdout)

    async def should_restart(self) -> Optional[List[Path]]:
        changes = await self.watcher.__anext__()
        if changes:
            unique_paths = {Path(c[1]) for c in changes}
            return [p for p in unique_paths if self.watch_filter(p)]
        return None

    def handle_exit(self, sig, frame):
        if WINDOWS and self.is_restarting:
            self.is_restarting = False
        else:
            self.should_exit.set()

    def _display_path(self, path: Path) -> str:
        try:
            return f'"{path.relative_to(self.cwd)}"'
        except ValueError:
            return f'"{path}"'
