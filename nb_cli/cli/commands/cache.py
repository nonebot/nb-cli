from pathlib import Path
from typing import Literal, cast

import click
from noneprompt import Choice, ListPrompt, CancelledError

from nb_cli import _
from nb_cli.handlers.data import CACHE_DIR
from nb_cli.cli.utils import humanize_data_size
from nb_cli.handlers import download_module_data
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_sync, run_async


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

    try:
        result = await ListPrompt(
            _("What do you want to do?"), choices=choices
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    sub_cmd = result.data
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
@run_async
async def status():
    click.echo(
        _("Cache location: {cache_dir}").format(cache_dir=str(CACHE_DIR.absolute()))
    )
    adapter_current = _filesize(CACHE_DIR / "adapters.json")
    adapter_unpublished = _filesize(CACHE_DIR / "adapters_unpublished.json")
    adapter_total = _filesize(
        CACHE_DIR / "adapters.json", CACHE_DIR / "adapters_unpublished.json"
    )
    driver_current = _filesize(CACHE_DIR / "drivers.json")
    driver_unpublished = _filesize(CACHE_DIR / "drivers_unpublished.json")
    driver_total = _filesize(
        CACHE_DIR / "drivers.json", CACHE_DIR / "drivers_unpublished.json"
    )
    plugin_current = _filesize(CACHE_DIR / "plugins.json")
    plugin_unpublished = _filesize(CACHE_DIR / "plugins_unpublished.json")
    plugin_total = _filesize(
        CACHE_DIR / "plugins.json", CACHE_DIR / "plugins_unpublished.json"
    )
    total_current = _filesize(
        CACHE_DIR / "adapters.json",
        CACHE_DIR / "drivers.json",
        CACHE_DIR / "plugins.json",
    )
    total_unpublished = _filesize(
        CACHE_DIR / "adapters_unpublished.json",
        CACHE_DIR / "drivers_unpublished.json",
        CACHE_DIR / "plugins_unpublished.json",
    )
    total_total = _filesize(
        CACHE_DIR / "adapters.json",
        CACHE_DIR / "adapters_unpublished.json",
        CACHE_DIR / "drivers.json",
        CACHE_DIR / "drivers_unpublished.json",
        CACHE_DIR / "plugins.json",
        CACHE_DIR / "plugins_unpublished.json",
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


@cache.command(name="update_all", help=_("Update all types of caches."))
@run_async
async def update_all():
    for mod in "adapter", "plugin", "driver":
        await _update_module_data(mod)


@cache.command(name="update_plugins", help=_("Update plugins cache."))
@run_async
async def update_plugins():
    await _update_module_data("plugin")


@cache.command(name="update_adapter", help=_("Update adapters cache."))
@run_async
async def update_adapters():
    await _update_module_data("adapter")


@cache.command(name="update_driver", help=_("Update driver cache."))
@run_async
async def update_drivers():
    await _update_module_data("driver")
