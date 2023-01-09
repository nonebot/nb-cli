from pathlib import Path
from typing import List, Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

from nb_cli.config import GLOBAL_CONFIG
from nb_cli.cli.utils import find_exact_package
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_sync, run_async
from nb_cli.handlers import (
    list_drivers,
    call_pip_update,
    call_pip_install,
    call_pip_uninstall,
    format_package_results,
)


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
@run_async
async def driver(ctx: click.Context):
    """Manage Bot Driver."""

    if ctx.invoked_subcommand is not None:
        return

    command = cast(ClickAliasedGroup, ctx.command)

    choices: List[Choice[click.Command]] = []
    for sub_cmd_name in await run_sync(command.list_commands)(ctx):
        if sub_cmd := await run_sync(command.get_command)(ctx, sub_cmd_name):
            choices.append(
                Choice(
                    sub_cmd.help or f"Run subcommand {sub_cmd.name}",
                    sub_cmd,
                )
            )

    try:
        result = await ListPrompt(
            "What do you want to do?", choices=choices
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    sub_cmd = result.data
    await run_sync(ctx.invoke)(sub_cmd)


@driver.command()
@run_async
async def list():
    """List nonebot drivers published on nonebot homepage."""
    drivers = await list_drivers()
    click.echo(format_package_results(drivers))


@driver.command()
@click.argument("name", nargs=1, default=None)
@run_async
async def search(name: Optional[str]):
    """Search for nonebot drivers published on nonebot homepage."""
    if name is None:
        name = await InputPrompt("Driver name to search:").prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    drivers = await list_drivers(name)
    click.echo(format_package_results(drivers))


@driver.command(aliases=["add"])
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    """Install nonebot driver to current project."""
    try:
        driver = await find_exact_package(
            "Driver name to install:", name, await list_drivers()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    if driver.project_link:
        proc = await call_pip_install(driver.project_link, pip_args)
        await proc.wait()


@driver.command()
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def update(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    """Update nonebot driver."""
    try:
        driver = await find_exact_package(
            "Driver name to update:", name, await list_drivers()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    if driver.project_link:
        proc = await call_pip_update(driver.project_link, pip_args)
        await proc.wait()


@driver.command(aliases=["remove"])
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def uninstall(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    """Uninstall nonebot driver from current project."""
    try:
        driver = await find_exact_package(
            "Driver name to uninstall:", name, await list_drivers()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    if package := driver.project_link:
        if package.startswith("nonebot2[") and package.endswith("]"):
            package = package[9:-1]
        proc = await call_pip_uninstall(driver.project_link, pip_args)
        await proc.wait()