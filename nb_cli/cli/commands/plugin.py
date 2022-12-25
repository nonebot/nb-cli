from pathlib import Path
from typing import List, Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup
from nb_cli.handlers import (
    list_plugins,
    create_plugin,
    call_pip_update,
    call_pip_install,
    call_pip_uninstall,
    print_package_results,
)

from .utils import find_exact_package


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
def plugin(ctx: click.Context):
    """Manage Bot Plugin."""

    if ctx.invoked_subcommand is not None:
        return

    command = cast(ClickAliasedGroup, ctx.command)

    choices: List[Choice[click.Command]] = []
    for sub_cmd_name in command.list_commands(ctx):
        if sub_cmd := command.get_command(ctx, sub_cmd_name):
            choices.append(
                Choice(
                    sub_cmd.help or f"Run subcommand {sub_cmd.name}",
                    sub_cmd,
                )
            )

    try:
        result = ListPrompt("What do you want to do?", choices=choices).prompt(
            style=CLI_DEFAULT_STYLE
        )
    except CancelledError:
        ctx.exit(0)

    sub_cmd = result.data
    ctx.invoke(sub_cmd)


@plugin.command()
def list():
    """List nonebot plugins published on nonebot homepage."""
    plugins = list_plugins()
    print_package_results(plugins)


@plugin.command()
@click.argument("name", nargs=1, default=None, help="Plugin name to search.")
def search(name: Optional[str]):
    """Search for nonebot plugin published on nonebot homepage."""
    if name is None:
        name = InputPrompt("Plugin name to search:").prompt(style=CLI_DEFAULT_STYLE)
    plugins = list_plugins(name)
    print_package_results(plugins)


@plugin.command(aliases=["add"])
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
def install(name: Optional[str], pip_args: Optional[List[str]]):
    """Install nonebot plugin to current project."""
    plugin = find_exact_package("Plugin name to install:", name, list_plugins())
    call_pip_install(plugin.project_link, pip_args)


@plugin.command()
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
def update(name: Optional[str], pip_args: Optional[List[str]]):
    """Update nonebot plugin."""
    plugin = find_exact_package("Plugin name to update:", name, list_plugins())
    call_pip_update(plugin.project_link, pip_args)


@plugin.command(aliases=["remove"])
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
def uninstall(name: Optional[str], pip_args: Optional[List[str]]):
    """Uninstall nonebot plugin from current project."""
    plugin = find_exact_package("Plugin name to uninstall:", name, list_plugins())
    call_pip_uninstall(plugin.project_link, pip_args)


@plugin.command(aliases=["new"])
@click.argument("name", default=None)
@click.option("-s", "--sub-plugin", is_flag=True, default=False)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None)
def create(
    name: Optional[str],
    sub_plugin: bool,
    output_dir: Optional[str],
    template: Optional[str],
):
    """Create a new nonebot plugin."""
    if name is None:
        name = InputPrompt("Plugin name:").prompt(style=CLI_DEFAULT_STYLE)
    if output_dir is None:
        detected: List[Choice[None]] = [
            Choice(str(d)) for d in Path(".").glob("**/plugins/") if d.is_dir()
        ]
        output_dir = (
            ListPrompt("Where to store the plugin?", detected + [Choice("Other")])
            .prompt(style=CLI_DEFAULT_STYLE)
            .name
        )
        if output_dir == "Other":
            output_dir = InputPrompt(
                "Output Dir:",
                validator=lambda x: len(x) > 0 and Path(x).is_dir(),
            ).prompt(style=CLI_DEFAULT_STYLE)
    create_plugin(name, output_dir, sub_plugin=sub_plugin, template=template)
