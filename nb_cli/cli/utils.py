from functools import wraps, partial
from collections.abc import Coroutine
from typing_extensions import ParamSpec
from typing import Any, Literal, TypeVar, Callable, Optional

import click
import anyio.to_thread
import anyio.from_thread
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
    question: str, name: Optional[str], packages: list[T]
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


def humanize_data_size(
    bytes_: int,
    *,
    precision: int = 3,
    threshold: float = 0.92,
    use_si: bool = False,
    negative_size: Literal["error", "n/a", "negative"] = "error",
) -> str:
    """
    Convert a byte count into a human-readable string (e.g., '1.23 MiB').

    Args:
        bytes_ (int): The number of bytes to convert.
        precision (int): Number of decimal places in the output.
        threshold (float): Factor used to determine when to switch to a higher unit.
        use_si (bool): If True, use base-1000 units (MB, GB); otherwise use
            base-1024 (MiB, GiB).
        negative_size: strategy to control how to process negative size.

    Returns:
        str: Human-readable size string.

    Raises:
        ValueError: If bytes_ is negative and `negative_size` is set 'error'.
    """
    neg = ""
    if bytes_ < 0:
        if negative_size == "error":
            raise ValueError("size should be no less than 0.")
        elif negative_size == "n/a":
            return "N/A"
        elif negative_size == "negative":
            bytes_ = -bytes_
            neg = "-"

    prefix = ["K", "M", "G", "T", "P", "E"]  # currently only 'M' is reachable at most
    if use_si:
        base = 1000
        unit = "B"
    else:
        base = 1024
        unit = "iB"

    unit_limit = base * threshold

    if bytes_ < unit_limit:
        return f"{neg}{bytes_} B"

    result: float = bytes_
    for p in prefix:
        result /= base
        if result < unit_limit:
            return f"{neg}{result:.{precision}g} {p}{unit}"

    return f"{neg}{result:.{precision}} {prefix[-1]}{unit}"  # size too large
