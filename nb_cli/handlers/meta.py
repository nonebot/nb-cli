import json
import asyncio
from functools import wraps
from typing_extensions import ParamSpec
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Union,
    TypeVar,
    Callable,
    Optional,
    Coroutine,
    cast,
)

from nb_cli import _, cache
from nb_cli.consts import REQUIRES_PYTHON
from nb_cli.exceptions import (
    PipNotInstalledError,
    PythonInterpreterError,
    NoneBotNotInstalledError,
)

from . import templates
from .config import ConfigManager
from .process import create_process

try:
    from pyfiglet import figlet_format
except ModuleNotFoundError as e:
    if e.name == "pkg_resources":
        raise ModuleNotFoundError("Please install setuptools to use pyfiglet")
    raise

R = TypeVar("R")
P = ParamSpec("P")

DEFAULT_PYTHON = ("python3", "python")
WINDOWS_DEFAULT_PYTHON = ("python",)


def draw_logo() -> str:
    return figlet_format("NoneBot", font="basic").strip()


if TYPE_CHECKING:

    async def get_default_python() -> str:
        ...

else:

    @cache(ttl=None)
    async def get_default_python() -> str:
        return ConfigManager(use_venv=False).get_python_path()


if TYPE_CHECKING:

    async def get_python_version(python_path: Optional[str] = None) -> Dict[str, int]:
        ...

else:

    @cache(ttl=None)
    async def get_python_version(python_path: Optional[str] = None) -> Dict[str, int]:
        if python_path is None:
            python_path = await get_default_python()

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
        return json.loads(stdout.strip())


def requires_python(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if "config_manager" in kwargs:
            python_path = await cast(
                ConfigManager, kwargs["config_manager"]
            ).get_python_path()
        else:
            python_path = cast(Union[str, None], kwargs.get("python_path"))
        version = await get_python_version(python_path=python_path)
        if (version["major"], version["minor"]) >= REQUIRES_PYTHON:
            return await func(*args, **kwargs)

        raise PythonInterpreterError(
            _("Python {major}.{minor} is not supported.").format(
                major=version["major"], minor=version["minor"]
            )
        )

    return wrapper


if TYPE_CHECKING:

    async def get_nonebot_version(python_path: Optional[str] = None) -> str:
        ...

else:

    @cache(ttl=None)
    async def get_nonebot_version(python_path: Optional[str] = None) -> str:
        if python_path is None:
            python_path = await get_default_python()

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
        return json.loads(stdout.strip())


def requires_nonebot(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    @requires_python
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if "config_manager" in kwargs:
            python_path = await cast(
                ConfigManager, kwargs["config_manager"]
            ).get_python_path()
        else:
            python_path = cast(Union[str, None], kwargs.get("python_path"))
        if await get_nonebot_version(python_path=python_path):
            return await func(*args, **kwargs)

        raise NoneBotNotInstalledError(_("NoneBot is not installed."))

    return wrapper


if TYPE_CHECKING:

    async def get_pip_version(python_path: Optional[str] = None) -> str:
        ...

else:

    @cache(ttl=None)
    async def get_pip_version(python_path: Optional[str] = None) -> str:
        if python_path is None:
            python_path = await get_default_python()

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
        return json.loads(stdout.strip())


def requires_pip(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    @requires_python
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if "config_manager" in kwargs:
            python_path = await cast(
                ConfigManager, kwargs["config_manager"]
            ).get_python_path()
        else:
            python_path = cast(Union[str, None], kwargs.get("python_path"))
        if await get_pip_version(python_path=python_path):
            return await func(*args, **kwargs)

        raise PipNotInstalledError(_("pip is not installed."))

    return wrapper
