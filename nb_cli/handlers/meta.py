import json
import asyncio
from pathlib import Path
from functools import wraps
from collections.abc import Coroutine
from typing_extensions import ParamSpec
from typing import TYPE_CHECKING, Any, TypeVar, Callable, Optional, cast

from nb_cli import _, cache
from nb_cli.consts import WINDOWS, REQUIRES_PYTHON
from nb_cli.config import GLOBAL_CONFIG, ConfigManager, NoneBotConfig
from nb_cli.exceptions import PipError, NoneBotError, PythonInterpreterError

from . import templates
from .process import create_process, create_process_shell

try:
    from pyfiglet import figlet_format
except ModuleNotFoundError as e:
    if e.name == "pkg_resources":
        raise ModuleNotFoundError("Please install setuptools to use pyfiglet") from e
    raise

R = TypeVar("R")
P = ParamSpec("P")

DEFAULT_PYTHON = ("python3", "python")
WINDOWS_DEFAULT_PYTHON = ("python",)


def draw_logo() -> str:
    return figlet_format("NoneBot", font="basic").strip()


def get_nonebot_config() -> NoneBotConfig:
    return GLOBAL_CONFIG.get_nonebot_config()


def get_project_root(cwd: Optional[Path] = None) -> Path:
    config = ConfigManager(working_dir=cwd) if cwd is not None else GLOBAL_CONFIG
    return config.project_root


def requires_project_root(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        get_project_root(cast(Optional[Path], kwargs.get("cwd")))
        return await func(*args, **kwargs)

    return wrapper


if TYPE_CHECKING:

    async def _get_env_python() -> str: ...

else:

    @cache(ttl=None)
    async def _get_env_python() -> str:
        python_to_try = WINDOWS_DEFAULT_PYTHON if WINDOWS else DEFAULT_PYTHON

        stdout, stderr = None, None

        for python in python_to_try:
            proc = await create_process_shell(
                f"{python} -W ignore -c "
                '"import sys, json; print(json.dumps(sys.executable))"',
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                try:
                    if executable := json.loads(stdout.splitlines()[-1].strip()):
                        return executable
                except Exception:
                    continue
        raise PythonInterpreterError(
            _("Cannot find a valid Python interpreter.")
            + (f"\nstdout:\n{stdout}" if stdout else "")
            + (f"\nstderr:\n{stderr}" if stderr else "")
        )


async def get_default_python(cwd: Optional[Path] = None) -> str:
    config = ConfigManager(working_dir=cwd) if cwd is not None else GLOBAL_CONFIG
    if config.python_path is not None:
        return config.python_path

    return await _get_env_python()


if TYPE_CHECKING:

    async def get_python_version(
        python_path: Optional[str] = None, cwd: Optional[Path] = None
    ) -> dict[str, int]: ...

else:

    @cache(ttl=None)
    async def get_python_version(
        python_path: Optional[str] = None, cwd: Optional[Path] = None
    ) -> dict[str, int]:
        if python_path is None:
            python_path = await get_default_python(cwd)

        t = templates.get_template("meta/python_version.py.jinja")
        proc = await create_process(
            python_path,
            "-W",
            "ignore",
            "-c",
            await t.render_async(),
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise PythonInterpreterError(
                _("Failed to get Python version.")
                + _("Exit code {code}").format(code=proc.returncode)
                + (f"\nstdout:\n{stdout}" if stdout else "")
                + (f"\nstderr:\n{stderr}" if stderr else "")
            )
        try:
            return json.loads(stdout.splitlines()[-1].strip())
        except Exception as e:
            raise PythonInterpreterError(
                _("Failed to get Python version.")
                + (f"\nstdout:\n{stdout}" if stdout else "")
                + (f"\nstderr:\n{stderr}" if stderr else "")
            ) from e


def requires_python(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        version = await get_python_version(
            cast(Optional[str], kwargs.get("python_path")),
            cast(Optional[Path], kwargs.get("cwd")),
        )
        if (version["major"], version["minor"]) >= REQUIRES_PYTHON:
            return await func(*args, **kwargs)

        raise PythonInterpreterError(
            _("Python {major}.{minor} is not supported.").format(
                major=version["major"], minor=version["minor"]
            )
        )

    return wrapper


if TYPE_CHECKING:

    async def get_nonebot_version(
        python_path: Optional[str] = None, cwd: Optional[Path] = None
    ) -> str: ...

else:

    @cache(ttl=None)
    async def get_nonebot_version(
        python_path: Optional[str] = None, cwd: Optional[Path] = None
    ) -> str:
        if python_path is None:
            python_path = await get_default_python(cwd)

        t = templates.get_template("meta/nonebot_version.py.jinja")
        proc = await create_process(
            python_path,
            "-W",
            "ignore",
            "-c",
            await t.render_async(),
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise NoneBotError(
                _("Failed to get NoneBot version.")
                + _("Exit code {code}").format(code=proc.returncode)
                + (f"\nstdout:\n{stdout}" if stdout else "")
                + (f"\nstderr:\n{stderr}" if stderr else "")
            )
        try:
            return json.loads(stdout.splitlines()[-1].strip())
        except Exception as e:
            raise NoneBotError(
                _("Failed to get NoneBot version.")
                + (f"\nstdout:\n{stdout}" if stdout else "")
                + (f"\nstderr:\n{stderr}" if stderr else "")
            ) from e


def requires_nonebot(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    @requires_python
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if await get_nonebot_version(
            cast(Optional[str], kwargs.get("python_path")),
            cast(Optional[Path], kwargs.get("cwd")),
        ):
            return await func(*args, **kwargs)

        raise NoneBotError(_("NoneBot is not installed."))

    return wrapper


if TYPE_CHECKING:

    async def get_pip_version(
        python_path: Optional[str] = None, cwd: Optional[Path] = None
    ) -> str: ...

else:

    @cache(ttl=None)
    async def get_pip_version(
        python_path: Optional[str] = None, cwd: Optional[Path] = None
    ) -> str:
        if python_path is None:
            python_path = await get_default_python(cwd)

        t = templates.get_template("meta/pip_version.py.jinja")
        proc = await create_process(
            python_path,
            "-W",
            "ignore",
            "-c",
            await t.render_async(),
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise PipError(
                _("Failed to get pip version.")
                + _("Exit code {code}").format(code=proc.returncode)
                + (f"\nstdout:\n{stdout}" if stdout else "")
                + (f"\nstderr:\n{stderr}" if stderr else "")
            )
        try:
            return json.loads(stdout.splitlines()[-1].strip())
        except Exception as e:
            raise PipError(
                _("Failed to get pip version.")
                + (f"\nstdout:\n{stdout}" if stdout else "")
                + (f"\nstderr:\n{stderr}" if stderr else "")
            ) from e


def requires_pip(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    @requires_python
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if await get_pip_version(
            cast(Optional[str], kwargs.get("python_path")),
            cast(Optional[Path], kwargs.get("cwd")),
        ):
            return await func(*args, **kwargs)

        raise PipError(_("pip is not installed."))

    return wrapper
