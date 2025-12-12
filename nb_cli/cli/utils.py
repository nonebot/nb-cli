import shutil
from statistics import median_high
from functools import wraps, partial
from typing_extensions import ParamSpec
from typing import Any, Literal, TypeVar, Protocol
from collections.abc import Callable, Iterable, Coroutine

import click
import anyio.to_thread
import anyio.from_thread
from wcwidth import wcswidth
from prompt_toolkit.styles import Style
from noneprompt import Choice, ListPrompt

from nb_cli import _
from nb_cli.config import Driver, Plugin, Adapter
from nb_cli.exceptions import NoSelectablePackageError

T = TypeVar("T", Adapter, Plugin, Driver)
P = ParamSpec("P")
R = TypeVar("R")
CT = TypeVar("CT", bound=str)

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


class _ValueFilterFunction(Protocol):
    def __call__(self, x: Adapter | Plugin | Driver, *, value: str) -> bool: ...


ADVANCED_SEARCH_FILTERS_SIMPLE: dict[
    str, Callable[[Adapter | Plugin | Driver], bool]
] = {
    "official": lambda x: x.is_official is True,
    "passing": lambda x: (
        not isinstance(x, Plugin) or x.valid is True or x.skip_test is True
    ),
}
ADVANCED_SEARCH_FILTERS_ARGS: dict[str, _ValueFilterFunction] = {
    "author:": lambda x, *, value: not value.strip()
    or any(v.lower() in x.author.lower() for v in value.strip().split(",")),
    "tag:": lambda x, *, value: not value.strip()
    or any(
        (v.lower() in (t.label.lower() for t in x.tags))
        for v in value.strip().split(",")
    ),
    "type:": lambda x, *, value: not value.strip()
    or not isinstance(x, Plugin)
    or value.strip() in "unknown"
    or (x.type is not None and value.strip() in x.type),
}


async def find_exact_package(
    question: str, name: str | None, packages: list[T], *, no_extras: bool = False
) -> T:
    if name is None:
        if not packages:
            raise NoSelectablePackageError("No packages available to select.")
        return (
            await ListPrompt(
                question,
                [
                    Choice(
                        "{name} ({desc})".format(
                            name=p.name, desc=p.desc.replace("\n", " ")
                        ),
                        p,
                    )
                    for p in packages
                ],
                custom_filter=lambda input_, p: advanced_search_filter(input_, p.data),
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        ).data

    if not no_extras and "[" in name:
        name = name.split("[", 1)[0].strip()

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
        click.echo(
            _("*** You may check with `--include-unpublished` option if supported.")
        )

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


def split_text_by_wcswidth(text: str, width: int):
    _width = width
    while wcswidth(text[:_width]) > width:
        _width = _width - 1
    return text[:_width], text[_width:]


def format_package_results(
    hits: list[T],
    name_column_width: int | None = None,
    terminal_width: int | None = None,
) -> str:
    if not hits:
        return ""

    if name_column_width is None:
        name_column_width = median_high(
            wcswidth(f"{hit.name} ({hit.project_link})") for hit in hits
        )
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size()[0]

    desc_width = terminal_width - name_column_width - 8

    lines: list[str] = []
    for hit in hits:
        is_official = "👍" if hit.is_official else "  "
        valid = "  "
        if isinstance(hit, Plugin):
            valid = "✅" if hit.valid else "❌"
        name = hit.name.replace("\n", "")
        link = f"({hit.project_link})"
        desc = hit.desc.replace("\n", "")
        # wrap and indent summary to fit terminal
        is_first_line = True
        while (
            wcswidth(f"{name} {link}") > name_column_width
            or wcswidth(desc) > desc_width
        ):
            name_column, name = split_text_by_wcswidth(name, name_column_width)
            if name_column == "":
                name_column, link = split_text_by_wcswidth(link, name_column_width)
            desc_column, desc = split_text_by_wcswidth(desc, desc_width)
            lines.append(
                name_column
                + " " * (name_column_width - wcswidth(name_column))
                + (f" {valid} {is_official} " if is_first_line else " " * 7)
                + desc_column
                + " " * (desc_width - wcswidth(desc_column))
            )
            is_first_line = False

        name_column = f"{name} {link}".strip()
        lines.append(
            name_column
            + " " * (name_column_width - wcswidth(name_column))
            + (f" {valid} {is_official} " if is_first_line else " " * 7)
            + desc
            + " " * (desc_width - wcswidth(desc))
        )

    return "\n".join(lines)


def auto_fgcolor(
    bg: str, gamma: float = 2.2, dark: CT = "#000000", light: CT = "#FFFFFF"
) -> CT:
    """Automatically choose black or white foreground color based on background color
    for optimal contrast.

    Args:
        bg (str): hex color string of the background color, in the format of "#RRGGBB".
        gamma (float): the gamma value to correct the luminance.
        dark (str): the dark color on brighter background, "#000000" by default.
        light (str): the light color on darker background, "#FFFFFF" by default.

    Returns:
        Either the `dark` color or the `bright` color.
    """
    # if 0.2126 × R**γ + 0.7152 × G**γ + 0.0722 × B**γ > 0.5**γ, choose black;
    #   else choose white.
    # See also: https://graphicdesign.stackexchange.com/questions/62368/automatically-select-a-foreground-color-based-on-a-background-color
    if len(bg) != 7:
        raise ValueError("Expected hex color string.")
    r_g, g_g, b_g = (
        float((int(x, base=16) / 255) ** gamma)
        for x in (bg.removeprefix("#")[i : i + 2] for i in (0, 2, 4))
    )
    luminance = 0.2126 * r_g + 0.7152 * g_g + 0.0722 * b_g
    return dark if luminance > (0.5**gamma) else light


def _advanced_search_filter(input_: str | list[str]) -> Callable[[T], bool]:
    if isinstance(input_, str):
        if ";" in input_[:1024]:
            return lambda module: any(
                _advanced_search_filter(_strip)(module)
                for sep in input_.split(";")
                if (_strip := sep.strip())
            )
        input_ = input_.split()

    def keyword_filter(m: T) -> bool:
        search_src = (
            m.project_link.lower(),
            m.module_name.lower(),
            m.name.lower(),
            m.desc.lower(),
        )
        return (
            not query_words
            or any(any(w.lower() in s for w in query_words) for s in search_src)
        ) and (
            not nquery_words
            or all(all(w.lower() not in s for w in nquery_words) for s in search_src)
        )

    filters: list[Callable[[T], bool]] = []
    nfilters: list[Callable[[T], bool]] = []
    query_words: set[str] = set()
    nquery_words: set[str] = set()

    for word in input_:
        if word and word[0] not in "#!":
            if word[0] != "-":
                query_words.add(word)
            elif word[1:]:
                nquery_words.add(word[1:])
            continue
        _filt = filters if word[0] == "#" else nfilters
        for stag, filter_ in ADVANCED_SEARCH_FILTERS_SIMPLE.items():
            if word[1:] == stag:
                _filt.append(filter_)
                continue
        for atag, filter_ in ADVANCED_SEARCH_FILTERS_ARGS.items():
            if word[1:].startswith(atag):
                _filt.append(partial(filter_, value=word[1:].removeprefix(atag)))
                continue

    return lambda module: (
        all(f(module) for f in filters)
        and not any(f(module) for f in nfilters)
        and keyword_filter(module)
    )


def advanced_search_filter(input_: str | list[str], module: T) -> bool:
    return _advanced_search_filter(input_)(module)


def advanced_search(input_: str | list[str], source: Iterable[T]) -> list[T]:
    filt = _advanced_search_filter(input_)
    return [m for m in source if filt(m)]


def cut_text(text: str, max_width: int, max_lines: int = 1) -> str:
    result: list[str] = []
    for __ in range(max_lines - 1):
        split, text = split_text_by_wcswidth(text, max_width)
        result.append(split)
    split, rest = split_text_by_wcswidth(text, max_width)
    if rest:
        split, _ = split_text_by_wcswidth(text, max_width - 3)
        result.append(split + "...")
    else:
        result.append(split)
    return "\n".join(result)
