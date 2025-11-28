import json
import typing
from datetime import datetime, timedelta
from asyncio import create_task, as_completed
from typing import TYPE_CHECKING, Literal, TypeVar, overload

import anyio
import click
import httpx

from nb_cli import _, cache
from nb_cli.handlers.data import CACHE_DIR
from nb_cli.config import Driver, Plugin, Adapter
from nb_cli.exceptions import ModuleLoadFailed, LocalCacheExpired
from nb_cli.compat import model_dump, type_validate_json, type_validate_python

T = TypeVar("T", Adapter, Plugin, Driver)

try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)  # ensure cache dir exists
except Exception:
    click.secho(_("WARNING: Cache directory is unavailable."), fg="yellow")


def _compile_module_index(modules: list[T]) -> dict[tuple[str, str], T]:
    return {(mod.name, mod.module_name): mod for mod in modules}


def _calculate_unpublished_modules(
    newer: list[T], current: list[T], historical_unpublished: list[T]
) -> list[T]:
    # NOTE: This function requires calculation.
    # Working with larger data can be slow, which is harmful to the async runtime.
    # Consider wrapping in something like to_thread if data size grows:
    # e.g., result = await asyncio.to_thread(
    #     get_unpublished_modules, newer, current, historical
    # )
    # or result = await anyio.to_process.run_sync(
    #     get_unpublished_modules
    # )(newer, current, historical)
    newer_index = _compile_module_index(newer)
    current_index = _compile_module_index(current + historical_unpublished)
    return [current_index[k] for k in set(current_index) - set(newer_index)]


async def dump_unpublished_modules(module_class: type[T], newer: list[T]) -> None:
    from nb_cli.cli.utils import run_sync  # avoid circular import error

    module_name: str = module_class.__module_name__

    if (path_current := CACHE_DIR / f"{module_name}.json").is_file():
        async with await anyio.open_file(path_current, encoding="utf-8") as fcurrent:
            current = type_validate_json(list[module_class], await fcurrent.read())
    else:
        current: list[T] = []

    if (path_historical := CACHE_DIR / f"{module_name}_unpublished.json").is_file():
        async with await anyio.open_file(
            path_historical, encoding="utf-8"
        ) as fhistorical:
            historical = type_validate_json(
                list[module_class], await fhistorical.read()
            )
    else:
        historical: list[T] = []

    result = await run_sync(_calculate_unpublished_modules)(newer, current, historical)
    async with await anyio.open_file(
        CACHE_DIR / f"{module_name}_unpublished.json", "w", encoding="utf-8"
    ) as fnew:
        await fnew.write(
            json.dumps([model_dump(x) for x in result], ensure_ascii=False)
        )


if TYPE_CHECKING:

    async def load_unpublished_modules(module_class: type[T]) -> list[T]: ...

else:

    @cache(ttl=None)
    async def load_unpublished_modules(module_class: type[T]) -> list[T]:
        module_name: str = module_class.__module_name__

        if (path_historical := CACHE_DIR / f"{module_name}_unpublished.json").is_file():
            async with await anyio.open_file(path_historical) as fhistorical:
                return type_validate_json(list[module_class], await fhistorical.read())
        return []


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
    ) -> list[Adapter] | list[Plugin] | list[Driver]: ...

else:

    @cache(ttl=None)
    async def download_module_data(
        module_type: Literal["adapter", "plugin", "driver"],
    ) -> list[Adapter] | list[Plugin] | list[Driver]:
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
                try:
                    await dump_unpublished_modules(module_class, result)  # type: ignore
                except Exception:
                    click.secho(
                        _(
                            "WARNING: Failed to update unpublished data for module "
                            "{module_type}."
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
) -> list[Adapter] | list[Plugin] | list[Driver]:
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

    datafile = CACHE_DIR / f"{module_name}.json"
    try:
        if allow_expired or datetime.now() - datetime.fromtimestamp(
            datafile.stat().st_mtime
        ) < timedelta(hours=12):
            return typing.cast(
                list[Adapter] | list[Plugin] | list[Driver],
                type_validate_json(list[module_class], datafile.read_text("utf-8")),
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
) -> list[Adapter] | list[Plugin] | list[Driver]:
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
