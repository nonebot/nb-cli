import abc
from pathlib import Path
from shutil import which
from collections.abc import Mapping, Sequence
from typing import IO, Literal, ClassVar, TypeAlias, overload

from packaging.requirements import Requirement

from nb_cli.cli.utils import run_sync
from nb_cli.config import ConfigManager
from nb_cli.exceptions import ProcessExecutionError

from .process import create_process
from .meta import get_project_root, requires_project_root

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

    available = next(iter(m for m in [current, *_manager_exec] if which(m) is not None))

    return current, available


class EnvironmentExecutor(metaclass=abc.ABCMeta):
    """Abstract base class for environment executors."""

    _executors: ClassVar[dict[str, type["EnvironmentExecutor"]]] = {}
    executable: ClassVar[str]
    cwd: Path
    stdin: FdFile | None
    stdout: FdFile | None
    stderr: FdFile | None
    env: Mapping[str, str] | None

    @abc.abstractmethod
    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.cwd = cwd
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.env = env

    def __init_subclass__(cls, /, *, name: str, **kwargs) -> None:
        cls._executors[name] = cls
        cls.executable = which(name) or name

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

    @abc.abstractmethod
    async def init(self, extra_args: Sequence[str | bytes] = ()) -> None:
        """Initialize the environment."""
        raise NotImplementedError("Init method is not implemented for this manager.")

    @abc.abstractmethod
    async def lock(self, extra_args: Sequence[str | bytes] = ()) -> None:
        """Generate or update the lock file for the environment."""
        raise NotImplementedError("Lock method is not implemented for this manager.")

    @abc.abstractmethod
    async def sync(self, extra_args: Sequence[str | bytes] = ()) -> None:
        """Synchronize the environment with the lock file or configuration."""
        raise NotImplementedError("Sync method is not implemented for this manager.")

    @abc.abstractmethod
    async def install(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        """Install packages into the environment.

        Args:
            packages: A list of package specifiers to install.
        """
        raise NotImplementedError("Install method is not implemented for this manager.")

    @abc.abstractmethod
    async def update(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        """Update packages in the environment.

        Args:
            packages: A list of package specifiers to update. If None, update all
                      packages.
        """
        raise NotImplementedError("Update method is not implemented for this manager.")

    @abc.abstractmethod
    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        """Uninstall packages from the environment.

        Args:
            packages: A list of package specifiers to uninstall.
        """
        raise NotImplementedError(
            "Uninstall method is not implemented for this manager."
        )


class UvEnvironmentExecutor(EnvironmentExecutor, name="uv"):
    """Environment executor for Uv environment manager."""

    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)

    async def init(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "uv",
            "init",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to initialize Uv environment.")

    async def lock(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "uv",
            "lock",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to lock Uv environment.")

    async def sync(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "uv",
            "sync",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync Uv environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "uv",
            "add",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to install packages in Uv environment.")

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "uv",
            "add",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to update packages in Uv environment.")

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "uv",
            "remove",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from Uv environment."
            )


class PdmEnvironmentExecutor(EnvironmentExecutor, name="pdm"):
    """Environment executor for PDM environment manager."""

    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)

    async def init(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "pdm",
            "init",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to initialize PDM environment.")

    async def lock(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "pdm",
            "lock",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to lock PDM environment.")

    async def sync(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "pdm",
            "sync",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync PDM environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "pdm",
            "add",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to install packages in PDM environment."
            )

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "pdm",
            "update",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to update packages in PDM environment.")

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "pdm",
            "remove",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from PDM environment."
            )


class PoetryEnvironmentExecutor(EnvironmentExecutor, name="poetry"):
    """Environment executor for Poetry environment manager."""

    def __init__(
        self,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)

    async def init(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "poetry",
            "init",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to initialize Poetry environment.")

    async def lock(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "poetry",
            "lock",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to lock Poetry environment.")

    async def sync(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "poetry",
            "install",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync Poetry environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "poetry",
            "add",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to install packages in Poetry environment."
            )

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "poetry",
            "update",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to update packages in Poetry environment."
            )

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "poetry",
            "remove",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from Poetry environment."
            )


class PipEnvironmentExecutor(EnvironmentExecutor, name="pip"):
    """Environment executor for Pip environment manager."""

    toml_manager: ConfigManager

    def __init__(
        self,
        toml_manager: ConfigManager,
        *,
        cwd: Path,
        stdin: FdFile | None = None,
        stdout: FdFile | None = None,
        stderr: FdFile | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env)
        self.toml_manager = toml_manager

    async def init(self, extra_args: Sequence[str | bytes] = ()) -> None:
        pass  # Pip does not require initialization.

    async def lock(self, extra_args: Sequence[str | bytes] = ()) -> None:
        pass  # Pip does not have a lock mechanism.

    async def sync(self, extra_args: Sequence[str | bytes] = ()) -> None:
        proc = await create_process(
            "pip",
            "install",
            ".",
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to sync Pip environment.")

    async def install(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "pip",
            "install",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to install packages in Pip environment."
            )
        self.toml_manager.add_dependency(*packages)

    async def update(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        proc = await create_process(
            "pip",
            "install",
            "--upgrade",
            *(str(pkg) for pkg in packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError("Failed to update packages in Pip environment.")
        self.toml_manager.update_dependency(*packages)

    async def uninstall(
        self, *packages: Requirement, extra_args: Sequence[str | bytes] = ()
    ) -> None:
        free_packages = self.toml_manager.remove_dependency(*packages)
        proc = await create_process(
            "pip",
            "uninstall",
            *(str(pkg) for pkg in free_packages),
            *extra_args,
            cwd=self.cwd,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            env=self.env,
        )
        if await proc.wait() != 0:
            raise ProcessExecutionError(
                "Failed to uninstall packages from Pip environment."
            )
