import abc
from pathlib import Path
from shutil import which
from asyncio.subprocess import Process
from collections.abc import Mapping, Sequence
from typing import IO, TYPE_CHECKING, Any, Union, Literal, ClassVar, TypeAlias, overload

import click
from packaging.requirements import Requirement

from nb_cli import _
from nb_cli.consts import WINDOWS
from nb_cli.cli.utils import run_sync
from nb_cli.exceptions import ProcessExecutionError
from nb_cli.config import GLOBAL_CONFIG, ConfigManager

from .process import create_process
from .meta import (
    DEFAULT_PYTHON,
    WINDOWS_DEFAULT_PYTHON,
    get_project_root,
    get_default_python,
    requires_project_root,
)

if TYPE_CHECKING:
    import os

_manager_features: dict[str, str] = {
    "uv": "uv.lock",
    "pdm": "pdm.lock",
    "poetry": "poetry.lock",
}
_manager_exec = [*_manager_features.keys(), "pip"]

FdFile: TypeAlias = int | IO[bytes] | IO[str]


@requires_project_root
@run_sync
def probe_environment_manager(*, cwd: Path | None = None) -> tuple[str, str]:
    """Probe the environment manager available and used in the current project.

    Returns:
        A tuple of (project_manager_inferred, available_manager).
    """
    project_root = get_project_root(cwd)

    current = next(
        iter(
            m for m, lock in _manager_features.items() if (project_root / lock).exists()
        ),
        "pip",
    )

    available = next(iter(m for m in [current, "pip"] if which(m) is not None))

    return current, available


@run_sync
def all_environment_managers() -> list[str]:
    """Get all available environment managers on the system.

    Returns:
        A list of available environment manager names.
    """
    return [m for m in _manager_exec if which(m) is not None]


class EnvironmentExecutor(metaclass=abc.ABCMeta):
    """Abstract base class for environment executors."""

    _executors: ClassVar[dict[str, type["EnvironmentExecutor"]]] = {}
    _executable: ClassVar[str]
    cwd: Path
    stdin: FdFile | None
    stdout: FdFile | None
    stderr: FdFile | None
    env: Mapping[str, str] | None
    executable: str

    @abc.abstractmethod
    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
        executable: str | None = None,
    ) -> None:
        self.cwd = cwd
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.executable = executable or self._executable
        self.env = env

    def __init_subclass__(cls, /, *, manager_name: str, **kwargs) -> None:
        cls._executors[manager_name] = cls
        cls._executable = which(manager_name) or manager_name

    async def run(
        self, *args: Union[str, bytes, "os.PathLike[str]", "os.PathLike[bytes]"]
    ) -> Process:
        """Run subprocess with the given parameters."""
        return await create_process(
            self.executable,
            *args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )

    @overload
    @classmethod
    def of(cls, name: Literal["uv"]) -> type["UvEnvironmentExecutor"]: ...
    @overload
    @classmethod
    def of(cls, name: Literal["pdm"]) -> type["PdmEnvironmentExecutor"]: ...
    @overload
    @classmethod
    def of(cls, name: Literal["poetry"]) -> type["PoetryEnvironmentExecutor"]: ...
    @overload
    @classmethod
    def of(cls, name: Literal["pip"]) -> type["PipEnvironmentExecutor"]: ...
    @overload
    @classmethod
    def of(cls, name: str) -> type["EnvironmentExecutor"]: ...

    @classmethod
    def of(cls, name: str) -> type["EnvironmentExecutor"]:
        """Get the executor class for the given environment manager name.

        Args:
            name: The name of the environment manager.
        Returns:
            The executor class corresponding to the given name.
        """
        try:
            return cls._executors[name]
        except KeyError as e:
            raise ValueError(f"Unknown environment manager: {name}") from e

    @classmethod
    @requires_project_root
    async def get(
        cls,
        name: str | None = None,
        *,
        toml_manager: ConfigManager = GLOBAL_CONFIG,
        cwd: Path | None = None,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
        executable: str | None = None,
    ) -> "EnvironmentExecutor":
        """Get an instance of the executor for the given environment manager name.

        Args:
            name: The name of the environment manager.
            cwd: The current working directory for the executor.
            stdin: The standard input for the executor.
            stdout: The standard output for the executor.
            stderr: The standard error for the executor.
            env: The environment variables for the executor.
            executable: The executable path for the environment manager.
        Returns:
            An instance of the executor corresponding to the given name.
        """
        if name is None:
            current, name = await probe_environment_manager(cwd=cwd)
            if current != name:
                click.secho(
                    _(
                        "Warning: The current project uses {current!r} "
                        "but the available manager is {name!r}."
                    ).format(current=current, name=name),
                    fg="yellow",
                )
        executor_cls = cls.of(name)
        extras: dict[str, Any]
        if name == "pip":
            if executable is None:
                executable = await get_default_python(cwd=cwd)
            extras = {"toml_manager": toml_manager}
        else:
            extras = {}
        return executor_cls(
            **extras,
            cwd=cwd or get_project_root(),
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env=env,
            executable=executable,
        )

    @abc.abstractmethod
    async def init(self, extra_args: Sequence[str] = ()) -> None:
        """Initialize the environment."""
        raise NotImplementedError("Init method is not implemented for this manager.")

    @abc.abstractmethod
    async def lock(self, extra_args: Sequence[str] = ()) -> None:
        """Generate or update the lock file for the environment."""
        raise NotImplementedError("Lock method is not implemented for this manager.")

    @abc.abstractmethod
    async def sync(self, extra_args: Sequence[str] = ()) -> None:
        """Synchronize the environment with the lock file or configuration."""
        raise NotImplementedError("Sync method is not implemented for this manager.")

    @abc.abstractmethod
    async def install(
        self, *packages: Requirement, extra_args: Sequence[str] = (), dev: bool = False
    ) -> None:
        """Install packages into the environment.

        Args:
            packages: A list of package specifiers to install.
        """
        raise NotImplementedError("Install method is not implemented for this manager.")

    @abc.abstractmethod
    async def update(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        """Update packages in the environment.

        Args:
            packages: A list of package specifiers to update. If None, update all
                      packages.
        """
        raise NotImplementedError("Update method is not implemented for this manager.")

    @abc.abstractmethod
    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        """Uninstall packages from the environment.

        Args:
            packages: A list of package specifiers to uninstall.
        """
        raise NotImplementedError(
            "Uninstall method is not implemented for this manager."
        )


class UvEnvironmentExecutor(EnvironmentExecutor, manager_name="uv"):
    """Environment executor for Uv environment manager."""

    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
        executable: str | None = None,
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)

    async def init(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("init", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to initialize Uv environment.")

    async def lock(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("lock", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to lock Uv environment.")

    async def sync(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("sync", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync Uv environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str] = (), dev: bool = False
    ) -> None:
        if dev:
            extra_args = (*extra_args, "--dev")
        proc = await self.run("add", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to install packages in Uv environment.")

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        proc = await self.run(
            "add", "--upgrade", *(str(pkg) for pkg in packages), *extra_args
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to update packages in Uv environment.")

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        proc = await self.run("remove", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from Uv environment."
            )


class PdmEnvironmentExecutor(EnvironmentExecutor, manager_name="pdm"):
    """Environment executor for PDM environment manager."""

    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
        executable: str | None = None,
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)

    async def init(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("init", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to initialize PDM environment.")

    async def lock(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("lock", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to lock PDM environment.")

    async def sync(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("sync", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync PDM environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str] = (), dev: bool = False
    ) -> None:
        if dev:
            extra_args = (*extra_args, "--dev")
        proc = await self.run("add", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to install packages in PDM environment."
            )

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        proc = await self.run("update", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to update packages in PDM environment.")

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await self.run("remove", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from PDM environment."
            )


class PoetryEnvironmentExecutor(EnvironmentExecutor, manager_name="poetry"):
    """Environment executor for Poetry environment manager."""

    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
        executable: str | None = None,
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)

    async def init(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("init", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to initialize Poetry environment.")

    async def lock(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("lock", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to lock Poetry environment.")

    async def sync(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("install", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync Poetry environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str] = (), dev: bool = False
    ) -> None:
        if dev:
            extra_args = (*extra_args, "--dev")
        proc = await self.run("add", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to install packages in Poetry environment."
            )

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        proc = await self.run("update", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to update packages in Poetry environment."
            )

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        proc = await self.run("remove", *(str(pkg) for pkg in packages), *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from Poetry environment."
            )


class PipEnvironmentExecutor(EnvironmentExecutor, manager_name="pip"):
    """Environment executor for Pip environment manager."""

    toml_manager: ConfigManager

    def __init__(
        self,
        toml_manager: ConfigManager = GLOBAL_CONFIG,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
        executable: str = WINDOWS_DEFAULT_PYTHON[0] if WINDOWS else DEFAULT_PYTHON[0],
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)
        self.executable = executable
        self.toml_manager = toml_manager

    async def init(self, extra_args: Sequence[str] = ()) -> None:
        pass  # Pip does not require initialization.

    async def lock(self, extra_args: Sequence[str] = ()) -> None:
        pass  # Pip does not have a lock mechanism.

    async def sync(self, extra_args: Sequence[str] = ()) -> None:
        proc = await self.run("-m", "pip", "install", "-e", ".", *extra_args)
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync Pip environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str] = (), dev: bool = False
    ) -> None:
        proc = await self.run(
            "-m", "pip", "install", *(str(pkg) for pkg in packages), *extra_args
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to install packages in Pip environment."
            )
        self.toml_manager.add_dependency(*packages, group="dev" if dev else None)

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        proc = await self.run(
            "-m",
            "pip",
            "install",
            "--upgrade",
            *(str(pkg) for pkg in packages),
            *extra_args,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to update packages in Pip environment.")
        self.toml_manager.update_dependency(*packages)

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str] = ()
    ) -> None:
        free_packages = self.toml_manager.remove_dependency(*packages)
        if not free_packages:
            return
        proc = await self.run(
            "-m", "pip", "uninstall", *(str(pkg) for pkg in free_packages), *extra_args
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from Pip environment."
            )
