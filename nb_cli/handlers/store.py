import json
import shutil
import typing
from statistics import median_high
from datetime import datetime, timedelta
from asyncio import create_task, as_completed
from typing import TYPE_CHECKING, Union, Literal, TypeVar, Optional, overload

import anyio
import click
import httpx
from wcwidth import wcswidth

from nb_cli import _, cache
from nb_cli.handlers.data import CACHE_DIR
from nb_cli.config import Driver, Plugin, Adapter
from nb_cli.exceptions import ModuleLoadFailed, LocalCacheExpired
from nb_cli.compat import type_validate_json, type_validate_python

T = TypeVar("T", Adapter, Plugin, Driver)

try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)  # ensure cache dir exists
except Exception:
    click.secho(_("WARNING: Cache directory is unavailable."), fg="yellow")


if TYPE_CHECKING:

    @overload
    async def download_module_data(
        module_type: Literal["adapter"],
    ) -> list[Adapter]: ...

    @overload
    async def download_module_data(module_type: Literal["plugin"]) -> list[Plugin]: ...

    @overload
    async def download_module_data(module_type: Literal["driver"]) -> list[Driver]: ...

    async def download_module_data(
        module_type: Literal["adapter", "plugin", "driver"],
    ) -> Union[list[Adapter], list[Plugin], list[Driver]]: ...

else:

    @cache(ttl=None)
    async def download_module_data(
        module_type: Literal["adapter", "plugin", "driver"],
    ) -> Union[list[Adapter], list[Plugin], list[Driver]]:
        if module_type == "adapter":
            module_class = Adapter
        elif module_type == "plugin":
            module_class = Plugin
        elif module_type == "driver":
            module_class = Driver
        else:
            raise ValueError(
                _("Invalid module type: {module_type}").format(module_type=module_type)
            )
        module_name: str = module_class.__module_name__

        exceptions: list[Exception] = []
        urls = [
            f"https://registry.nonebot.dev/{module_name}.json",
            f"https://cdn.jsdelivr.net/gh/nonebot/registry@results/{module_name}.json",
            f"https://cdn.staticaly.com/gh/nonebot/registry@results/{module_name}.json",
            f"https://jsd.cdn.zzko.cn/gh/nonebot/registry@results/{module_name}.json",
            f"https://mirror.ghproxy.com/https://raw.githubusercontent.com/nonebot/registry/results/{module_name}.json",
            f"https://gh-proxy.com/https://raw.githubusercontent.com/nonebot/registry/results/{module_name}.json",
        ]

        async def _request(url: str) -> httpx.Response:
            async with httpx.AsyncClient() as client:
                return await client.get(url)

        tasks = [create_task(_request(url)) for url in urls]
        for future in as_completed(tasks):
            try:
                resp = await future
                items = resp.json()
                result = type_validate_python(list[module_class], items)
                for task in tasks:
                    if not task.done():
                        task.cancel()
                try:
                    # attempt to save cache, pass even if failed
                    async with await anyio.open_file(
                        CACHE_DIR / f"{module_name}.json", "w", encoding="utf-8"
                    ) as f:
                        await f.write(json.dumps(items, ensure_ascii=False))
                except Exception:
                    click.secho(
                        _(
                            "WARNING: Failed to cache data for module {module_type}."
                        ).format(module_type=module_type),
                        fg="yellow",
                    )
                return result  # type: ignore
            except Exception as e:
                exceptions.append(e)

        raise ModuleLoadFailed(
            _("Failed to get {module_type} list.").format(module_type=module_type),
            exceptions,
        )


@overload
def load_local_module_data(
    module_type: Literal["adapter"], *, allow_expired: bool = False
) -> list[Adapter]: ...


@overload
def load_local_module_data(
    module_type: Literal["plugin"], *, allow_expired: bool = False
) -> list[Plugin]: ...


@overload
def load_local_module_data(
    module_type: Literal["driver"], *, allow_expired: bool = False
) -> list[Driver]: ...


def load_local_module_data(
    module_type: Literal["adapter", "plugin", "driver"],
    *,
    allow_expired: bool = False,
) -> Union[list[Adapter], list[Plugin], list[Driver]]:
    if module_type == "adapter":
        ModuleClass = Adapter
    elif module_type == "plugin":
        ModuleClass = Plugin
    elif module_type == "driver":
        ModuleClass = Driver
    else:
        raise ValueError(
            _("Invalid module type: {module_type}").format(module_type=module_type)
        )
    module_name: str = ModuleClass.__module_name__

    datafile = CACHE_DIR / f"{module_name}.json"
    try:
        if allow_expired or datetime.now() - datetime.fromtimestamp(
            datafile.stat().st_mtime
        ) < timedelta(hours=12):
            return typing.cast(
                Union[list[Adapter], list[Plugin], list[Driver]],
                type_validate_json(list[ModuleClass], datafile.read_text("utf-8")),
            )
    except Exception as exc:
        raise ModuleLoadFailed(
            _("Invalid local cache of module type: {module_type}").format(
                module_type=module_type
            ),
            exc,
        )
    raise LocalCacheExpired()


@overload
async def load_module_data(module_type: Literal["adapter"]) -> list[Adapter]: ...


@overload
async def load_module_data(module_type: Literal["plugin"]) -> list[Plugin]: ...


@overload
async def load_module_data(module_type: Literal["driver"]) -> list[Driver]: ...


async def load_module_data(
    module_type: Literal["adapter", "plugin", "driver"],
) -> Union[list[Adapter], list[Plugin], list[Driver]]:
    try:
        return load_local_module_data(module_type)
    except ModuleLoadFailed:  # local cache file is missing or broken
        return await download_module_data(module_type)
    except LocalCacheExpired:  # local cache file is expired
        pass  # continue trying

    try:
        return await download_module_data(module_type)
    except ModuleLoadFailed:
        res = load_local_module_data(module_type, allow_expired=True)
        click.secho(
            _(
                "WARNING: Failed to download latest data of module {module_type}. "
                "Expired cache is used."
            ).format(module_type=module_type),
            fg="yellow",
        )
        return res


def split_text_by_wcswidth(text: str, width: int):
    _width = width
    while wcswidth(text[:_width]) > width:
        _width = _width - 1
    return text[:_width], text[_width:]


def format_package_results(
    hits: list[T],
    name_column_width: Optional[int] = None,
    terminal_width: Optional[int] = None,
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
