from pathlib import Path
from typing import List, Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

from nb_cli.cli.utils import find_exact_package
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_sync, run_async
from nb_cli.handlers import (
    list_adapters,
    create_adapter,
    call_pip_update,
    call_pip_install,
    call_pip_uninstall,
    get_config_manager,
    format_package_results,
)


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
@run_async
async def adapter(ctx: click.Context):
    """Manage Bot Adapter."""

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
        ctx.exit(0)

    sub_cmd = result.data
    await run_sync(ctx.invoke)(sub_cmd)


@adapter.command()
@run_async
async def list():
    """List nonebot adapters published on nonebot homepage."""
    adapters = await list_adapters()
    click.echo(format_package_results(adapters))


@adapter.command()
@click.argument("name", nargs=1, default=None)
@run_async
async def search(name: Optional[str]):
    """Search for nonebot adapter published on nonebot homepage."""
    if name is None:
        name = await InputPrompt("Adapter name to search:").prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    adapters = await list_adapters(name)
    click.echo(format_package_results(adapters))


@adapter.command(aliases=["add"])
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def install(name: Optional[str], pip_args: Optional[List[str]]):
    """Install nonebot adapter to current project."""
    adapter = await find_exact_package(
        "Adapter name to install:", name, await list_adapters()
    )
    try:
        get_config_manager().add_adapter(adapter)
    except RuntimeError as e:
        click.echo(f"Failed to add adapter {adapter.name} to config: {e}")

    await call_pip_install(adapter.project_link, pip_args)


@adapter.command()
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def update(name: Optional[str], pip_args: Optional[List[str]]):
    """Update nonebot adapter."""
    adapter = await find_exact_package(
        "Adapter name to update:", name, await list_adapters()
    )
    await call_pip_update(adapter.project_link, pip_args)


@adapter.command(aliases=["remove"])
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def uninstall(name: Optional[str], pip_args: Optional[List[str]]):
    """Uninstall nonebot adapter from current project."""
    adapter = await find_exact_package(
        "Adapter name to uninstall:", name, await list_adapters()
    )

    try:
        get_config_manager().remove_adapter(adapter)
    except RuntimeError as e:
        click.echo(f"Failed to remove adapter {adapter.name} from config: {e}")

    await call_pip_uninstall(adapter.project_link, pip_args)


@adapter.command(aliases=["new"])
@click.argument("name", default=None)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None)
@run_async
async def create(
    name: Optional[str],
    output_dir: Optional[str],
    template: Optional[str],
):
    """Create a new nonebot adapter."""
    if name is None:
        name = await InputPrompt("Adapter name:").prompt_async(style=CLI_DEFAULT_STYLE)
    if output_dir is None:
        detected: List[Choice[None]] = [
            Choice(str(x)) for x in Path(".").glob("**/adapters/") if x.is_dir()
        ] or [
            Choice(f"{x}/adapters/")
            for x in Path(".").glob("*/")
            if x.is_dir() and not x.name.startswith(".") and not x.name.startswith("_")
        ]
        output_dir = (
            await ListPrompt(
                "Where to store the adapter?", detected + [Choice("Other")]
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        ).name
        if output_dir == "Other":
            output_dir = await InputPrompt(
                "Output Dir:",
                validator=lambda x: len(x) > 0 and Path(x).is_dir(),
            ).prompt_async(style=CLI_DEFAULT_STYLE)
    elif not Path(output_dir).is_dir():
        click.secho("Output dir is not a directory!", fg="yellow")
        output_dir = await InputPrompt(
            "Adapter Dir:", validator=lambda x: len(x) > 0 and Path(x).is_dir()
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    create_adapter(name, output_dir, template=template)
