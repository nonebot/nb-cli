from functools import wraps, partial
from typing_extensions import ParamSpec
from typing import Any, List, TypeVar, Callable, Optional, Coroutine

import anyio
import click
from noneprompt import InputPrompt
from prompt_toolkit.styles import Style

from nb_cli import _
from nb_cli.config import Driver, Plugin, Adapter
from nb_cli.handlers import format_package_results

T = TypeVar("T", Adapter, Plugin, Driver)
P = ParamSpec("P")
R = TypeVar("R")

CLI_DEFAULT_STYLE = Style.from_dict(
    {
        "questionmark": "fg:#673AB7 bold",
        "question": "",
        "sign": "",
        "unsign": "",
        "selected": "",
        "pointer": "bold",
        "annotation": "",
        "answer": "bold",
    }
)


async def find_exact_package(
    question: str, name: Optional[str], packages: List[T]
) -> T:
    if name is None:
        name = await InputPrompt(question).prompt_async(style=CLI_DEFAULT_STYLE)

    if exact_packages := [
        p for p in packages if name in {p.name, p.module_name, p.project_link}
    ]:
        return exact_packages[0]

    packages = [
        p
        for p in packages
        if name in p.name or name in p.module_name or name in p.project_link
    ]
    if len(packages) == 1:
        return packages[0]
    elif len(packages) > 1:
        click.echo(format_package_results(packages))
    else:
        click.echo(_("Package {name} not found.").format(name=name))

    raise RuntimeError("No or multiple packages found.")


def run_sync(func: Callable[P, R]) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return await anyio.to_thread.run_sync(partial(func, *args, **kwargs))

    return wrapper


def run_async(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return anyio.from_thread.run(partial(func, *args, **kwargs))

    return wrapper
