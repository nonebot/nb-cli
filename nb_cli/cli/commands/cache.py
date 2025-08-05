import os
from pathlib import Path
from typing import Literal, cast

import click
from noneprompt import Choice, ListPrompt, ConfirmPrompt, CancelledError

from nb_cli import _
from nb_cli import cache as cache_data
from nb_cli.handlers.data import CACHE_DIR
from nb_cli.cli.utils import humanize_data_size
from nb_cli.handlers import download_module_data
from nb_cli.cli import (
    CLI_DEFAULT_STYLE,
    ClickAliasedGroup,
    back_,
    exit_,
    run_sync,
    run_async,
)


@click.group(
    cls=ClickAliasedGroup,
    invoke_without_command=True,
    help=_("Manage CLI data caches."),
)
@click.pass_context
@run_async
async def cache(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    command = cast(ClickAliasedGroup, ctx.command)

    choices: list[Choice[click.Command]] = []
    for sub_cmd_name in await run_sync(command.list_commands)(ctx):
        if sub_cmd := await run_sync(command.get_command)(ctx, sub_cmd_name):
            choices.append(
                Choice(
                    sub_cmd.help
                    or _("Run subcommand {sub_cmd.name!r}").format(sub_cmd=sub_cmd),
                    sub_cmd,
                )
            )
    if ctx.parent and ctx.parent.params.get("can_back_to_parent", False):
        _exit_choice = Choice(_("Back to top level."), back_)
    else:
        _exit_choice = Choice(_("Exit NB CLI."), exit_)
    choices.append(_exit_choice)

    while True:
        try:
            result = await ListPrompt(
                _("What do you want to do?"), choices=choices
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            result = _exit_choice

        sub_cmd = result.data
        if sub_cmd == back_:
            return
        ctx.params["can_back_to_parent"] = True
        await run_sync(ctx.invoke)(sub_cmd)


def _filesize(
    *path: Path, nonexist: Literal[0, -1] = -1, precision: int = 3, si: bool = False
) -> str:
    if not any(p.is_file() for p in path):
        size = nonexist
    else:
        size = sum(p.stat().st_size for p in path if p.is_file())

    return humanize_data_size(size, precision=precision, use_si=si, negative_size="n/a")


@cache.command(name="status", help=_("Show current usage of caches."))
@click.option(
    "--si",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Show sizes under 1000-based SI units."),
)
@run_async
async def status(si: bool = False):
    click.echo(
        _("Cache location: {cache_dir}").format(cache_dir=str(CACHE_DIR.absolute()))
    )
    adapter_current = _filesize(CACHE_DIR / "adapters.json", si=si)
    adapter_unpublished = _filesize(CACHE_DIR / "adapters_unpublished.json", si=si)
    adapter_total = _filesize(
        CACHE_DIR / "adapters.json", CACHE_DIR / "adapters_unpublished.json", si=si
    )
    driver_current = _filesize(CACHE_DIR / "drivers.json", si=si)
    driver_unpublished = _filesize(CACHE_DIR / "drivers_unpublished.json", si=si)
    driver_total = _filesize(
        CACHE_DIR / "drivers.json", CACHE_DIR / "drivers_unpublished.json", si=si
    )
    plugin_current = _filesize(CACHE_DIR / "plugins.json", si=si)
    plugin_unpublished = _filesize(CACHE_DIR / "plugins_unpublished.json", si=si)
    plugin_total = _filesize(
        CACHE_DIR / "plugins.json", CACHE_DIR / "plugins_unpublished.json", si=si
    )
    total_current = _filesize(
        CACHE_DIR / "adapters.json",
        CACHE_DIR / "drivers.json",
        CACHE_DIR / "plugins.json",
        si=si,
    )
    total_unpublished = _filesize(
        CACHE_DIR / "adapters_unpublished.json",
        CACHE_DIR / "drivers_unpublished.json",
        CACHE_DIR / "plugins_unpublished.json",
        si=si,
    )
    total_total = _filesize(
        CACHE_DIR / "adapters.json",
        CACHE_DIR / "adapters_unpublished.json",
        CACHE_DIR / "drivers.json",
        CACHE_DIR / "drivers_unpublished.json",
        CACHE_DIR / "plugins.json",
        CACHE_DIR / "plugins_unpublished.json",
        si=si,
    )
    click.echo(_("Module Type     Current         Unpublished     Total"))
    click.echo(
        _(
            "Adapter         {adapter_current:<15} {adapter_unpublished:<15} "
            "{adapter_total:<15}"
        ).format(
            adapter_current=adapter_current,
            adapter_unpublished=adapter_unpublished,
            adapter_total=adapter_total,
        )
    )
    click.echo(
        _(
            "Driver          {driver_current:<15} {driver_unpublished:<15} "
            "{driver_total:<15}"
        ).format(
            driver_current=driver_current,
            driver_unpublished=driver_unpublished,
            driver_total=driver_total,
        )
    )
    click.echo(
        _(
            "Plugin          {plugin_current:<15} {plugin_unpublished:<15} "
            "{plugin_total:<15}"
        ).format(
            plugin_current=plugin_current,
            plugin_unpublished=plugin_unpublished,
            plugin_total=plugin_total,
        )
    )
    click.echo(
        _(
            "(Total)         {total_current:<15} {total_unpublished:<15} "
            "{total_total:<15}"
        ).format(
            total_current=total_current,
            total_unpublished=total_unpublished,
            total_total=total_total,
        )
    )


async def _update_module_data(module_type: Literal["adapter", "plugin", "driver"]):
    try:
        await download_module_data(module_type)
    except Exception:
        click.secho(
            _("ERROR: Failed to update data cache for module {module_type}.").format(
                module_type=module_type
            ),
            fg="red",
        )
    else:
        click.echo(
            _("Successfully updated data cache for module {module_type}.").format(
                module_type=module_type
            )
        )


@cache.command(name="update", help=_("Update local cache."))
@click.argument("module_type", type=str, nargs=1, default="all")
@run_async
async def update(module_type: str):
    await cache_data.clear()
    if module_type == "all":
        for mod in "adapter", "plugin", "driver":
            await _update_module_data(mod)
        return

    if module_type not in ("adapter", "plugin", "driver"):
        click.secho(
            _("ERROR: Invalid module type: {module_type}").format(
                module_type=module_type
            ),
            fg="red",
        )
        return
    await _update_module_data(module_type)


@cache.command(name="update-adapter", help=_("Update local cache for adapters."))
@click.pass_context
@run_async
async def update_adapter(ctx: click.Context):
    await run_sync(ctx.invoke)(update, module_type="adapter")


@cache.command(name="update-plugin", help=_("Update local cache for plugins."))
@click.pass_context
@run_async
async def update_plugin(ctx: click.Context):
    await run_sync(ctx.invoke)(update, module_type="plugin")


@cache.command(name="update-driver", help=_("Update local cache for drivers."))
@click.pass_context
@run_async
async def update_driver(ctx: click.Context):
    await run_sync(ctx.invoke)(update, module_type="driver")


@cache.command(
    name="clear-unpublished", help=_("Clear local caches of unpublished modules.")
)
@click.option(
    "-y",
    "--noconfirm",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Clear caches without confirm."),
)
@click.pass_context
@run_async
async def clear_unpublished(ctx: click.Context, noconfirm: bool = False):
    await run_sync(ctx.invoke)(clear, unpublished_only=True, noconfirm=noconfirm)


@cache.command(name="clear", help=_("Clear local caches."))
@click.option(
    "--unpublished-only",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Only clear caches for unpublished module types."),
)
@click.option(
    "-y",
    "--noconfirm",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Clear caches without confirm."),
)
@run_async
async def clear(unpublished_only: bool = False, noconfirm: bool = False):
    if not noconfirm:
        confirm = await ConfirmPrompt(
            _("Are you sure to clear these caches?"), default_choice=True
        ).prompt_async(style=CLI_DEFAULT_STYLE)
        if not confirm:
            return

    await cache_data.clear()

    for f in (
        CACHE_DIR / "adapters_unpublished.json",
        CACHE_DIR / "drivers_unpublished.json",
        CACHE_DIR / "plugins_unpublished.json",
    ):
        if f.is_file():
            await run_sync(os.remove)(f)

    if unpublished_only:
        click.echo(_("Successfully cleared unpublished caches."))
        return

    for f in (
        CACHE_DIR / "adapters.json",
        CACHE_DIR / "drivers.json",
        CACHE_DIR / "plugins.json",
    ):
        if f.is_file():
            await run_sync(os.remove)(f)

    click.echo(_("Successfully cleared all caches."))
