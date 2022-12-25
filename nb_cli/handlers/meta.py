import json
import shutil
import contextlib
import subprocess
from pathlib import Path
from functools import wraps, lru_cache
from typing_extensions import ParamSpec
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Type,
    Union,
    Literal,
    TypeVar,
    Callable,
    Optional,
    overload,
)

import click
import httpx
from wcwidth import wcswidth
from pyfiglet import figlet_format

from nb_cli.consts import CONFIG_KEY, REQUIRES_PYTHON
from nb_cli.config import Config, Driver, Plugin, Adapter, ConfigManager
from nb_cli.exceptions import (
    ModuleLoadFailed,
    PythonVersionError,
    PipNotInstalledError,
    NoneBotNotInstalledError,
)

from . import templates

T = TypeVar("T", Adapter, Plugin, Driver)
R = TypeVar("R")
P = ParamSpec("P")


def draw_logo() -> str:
    return figlet_format("NoneBot", font="basic").strip()


def get_config() -> Config:
    if ctx := click.get_current_context(silent=True):
        return ctx.meta[CONFIG_KEY]
    return ConfigManager(Path("pyproject.toml")).get_config()


if TYPE_CHECKING:

    def get_python_version(python_path: Optional[str] = None) -> Dict[str, int]:
        ...

else:

    @lru_cache()
    def get_python_version(python_path: Optional[str] = None) -> Dict[str, int]:
        if python_path is None:
            python_path = get_config().nb_cli.python

        t = templates.get_template("meta/python_version.py.jinja")
        return json.loads(
            subprocess.check_output([python_path, "-c", t.render()], text=True).strip()
        )


def requires_python(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        version = get_python_version()
        if (version["major"], version["minor"]) >= REQUIRES_PYTHON:
            return func(*args, **kwargs)

        raise PythonVersionError(
            f"Python {version['major']}.{version['minor']} is not supported."
        )

    return wrapper


if TYPE_CHECKING:

    def get_nonebot_version(python_path: Optional[str] = None) -> str:
        ...

else:

    @lru_cache()
    def get_nonebot_version(python_path: Optional[str] = None) -> str:
        if python_path is None:
            python_path = get_config().nb_cli.python

        t = templates.get_template("meta/nonebot_version.py.jinja")
        return json.loads(
            subprocess.check_output([python_path, "-c", t.render()], text=True).strip()
        )


def requires_nonebot(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    @requires_python
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if get_nonebot_version():
            return func(*args, **kwargs)

        raise NoneBotNotInstalledError("NoneBot is not installed.")

    return wrapper


if TYPE_CHECKING:

    def get_pip_version(python_path: Optional[str] = None) -> str:
        ...

else:

    @lru_cache()
    def get_pip_version(python_path: Optional[str] = None) -> str:
        if python_path is None:
            python_path = get_config().nb_cli.python

        t = templates.get_template("meta/pip_version.py.jinja")
        return json.loads(
            subprocess.check_output([python_path, "-c", t.render()], text=True).strip()
        )


def requires_pip(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    @requires_python
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if get_pip_version():
            return func(*args, **kwargs)

        raise PipNotInstalledError("pip is not installed.")

    return wrapper


if TYPE_CHECKING:

    @overload
    def load_module_data(module_type: Literal["adapter"]) -> List[Adapter]:
        ...

    @overload
    def load_module_data(module_type: Literal["plugin"]) -> List[Plugin]:
        ...

    @overload
    def load_module_data(module_type: Literal["driver"]) -> List[Driver]:
        ...

    def load_module_data(
        module_type: Literal["adapter", "plugin", "driver"]
    ) -> Union[List[Adapter], List[Plugin], List[Driver]]:
        ...

else:

    @lru_cache()
    def load_module_data(
        module_type: Literal["adapter", "plugin", "driver"]
    ) -> Union[List[Adapter], List[Plugin], List[Driver]]:
        if module_type == "adapter":
            module_class = Adapter
        elif module_type == "plugin":
            module_class = Plugin
        elif module_type == "driver":
            module_class = Driver
        else:
            raise ValueError(f"Invalid module type: {module_type}")
        module_name: str = getattr(module_class.__config__, "module_name")

        exceptions: List[Exception] = []
        urls = [
            f"https://v2.nonebot.dev/{module_name}.json",
            f"https://raw.fastgit.org/nonebot/nonebot2/master/website/static/{module_name}.json",
            f"https://cdn.jsdelivr.net/gh/nonebot/nonebot2/website/static/{module_name}.json",
        ]
        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = [executor.submit(httpx.get, url) for url in urls]

            for future in as_completed(tasks):
                try:
                    resp = future.result()
                    items = resp.json()
                    return [module_class.parse_obj(item) for item in items]  # type: ignore
                except Exception as e:
                    exceptions.append(e)

        raise ModuleLoadFailed(f"Failed to get {module_name} list.", exceptions)


def print_package_results(
    hits: List[T],
    name_column_width: Optional[int] = None,
    terminal_width: Optional[int] = None,
):
    if not hits:
        return

    if name_column_width is None:
        name_column_width = (
            max(wcswidth(f"{hit.name} ({hit.project_link})") for hit in hits) + 4
        )
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size()[0]

    for hit in hits:
        name = f"{hit.name} ({hit.project_link})"
        summary = hit.desc
        target_width = terminal_width - name_column_width - 5
        if target_width > 10:
            # wrap and indent summary to fit terminal
            summary_lines = []
            while wcswidth(summary) > target_width:
                tmp_length = target_width
                while wcswidth(summary[:tmp_length]) > target_width:
                    tmp_length = tmp_length - 1
                summary_lines.append(summary[:tmp_length])
                summary = summary[tmp_length:]
            summary_lines.append(summary)
            summary = ("\n" + " " * (name_column_width + 3)).join(summary_lines)

        line = f"{name + ' ' * (name_column_width - wcswidth(name))} - {summary}"
        with contextlib.suppress(UnicodeEncodeError):
            print(line)
