from pathlib import Path
from typing import List, Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, ConfirmPrompt, CancelledError

from nb_cli import _
from nb_cli.config import GLOBAL_CONFIG
from nb_cli.cli.utils import find_exact_package
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_sync, run_async
from nb_cli.handlers import (
    list_plugins,
    create_plugin,
    call_pip_update,
    call_pip_install,
    call_pip_uninstall,
    format_package_results,
)


@click.group(
    cls=ClickAliasedGroup, invoke_without_command=True, help=_("Manage bot plugins.")
)
@click.pass_context
@run_async
async def plugin(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    command = cast(ClickAliasedGroup, ctx.command)

    choices: List[Choice[click.Command]] = []
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


@plugin.command(help=_("List nonebot plugins published on nonebot homepage."))
@run_async
async def list():
    plugins = await list_plugins()
    click.echo(format_package_results(plugins))


@plugin.command(help=_("Search for nonebot plugins published on nonebot homepage."))
@click.argument("name", nargs=1, required=False, default=None)
@run_async
async def search(name: Optional[str]):
    if name is None:
        name = await InputPrompt(_("Plugin name to search:")).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    plugins = await list_plugins(name)
    click.echo(format_package_results(plugins))


@plugin.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install nonebot plugin to current project."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    try:
        plugin = await find_exact_package(
            _("Plugin name to install:"), name, await list_plugins()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.add_plugin(plugin.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to add plugin {plugin.name} to config: {e}").format(
                plugin=plugin, e=e
            )
        )

    proc = await call_pip_install(plugin.project_link, pip_args)
    await proc.wait()


@plugin.command(
    context_settings={"ignore_unknown_options": True}, help=_("Update nonebot plugin.")
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def update(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    try:
        plugin = await find_exact_package(
            _("Plugin name to update:"), name, await list_plugins()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    proc = await call_pip_update(plugin.project_link, pip_args)
    await proc.wait()


@plugin.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall nonebot plugin from current project."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def uninstall(
    ctx: click.Context, name: Optional[str], pip_args: Optional[List[str]]
):
    try:
        plugin = await find_exact_package(
            _("Plugin name to uninstall:"), name, await list_plugins()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.remove_plugin(plugin.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove plugin {plugin.name} from config: {e}").format(
                plugin=plugin, e=e
            )
        )

    proc = await call_pip_uninstall(plugin.project_link, pip_args)
    await proc.wait()


@plugin.command(aliases=["new"], help=_("Create a new nonebot plugin."))
@click.argument("name", nargs=1, required=False, default=None)
@click.option("-s", "--sub-plugin", is_flag=True, default=None)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help=_("The plugin template to use."))
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    name: Optional[str],
    sub_plugin: Optional[bool],
    output_dir: Optional[str],
    template: Optional[str],
):
    if name is None:
        try:
            name = await InputPrompt(_("Plugin name:")).prompt_async(
                style=CLI_DEFAULT_STYLE
            )
        except CancelledError:
            ctx.exit()
    if sub_plugin is None:
        try:
            sub_plugin = await ConfirmPrompt(
                _("Use nested plugin?"), default_choice=False
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    if output_dir is None:
        detected: List[Choice[None]] = [
            Choice(str(d))
            for d in Path(".").glob("**/plugins/")
            if d.is_dir()
            and not any(
                p.name.startswith("_") or p.name.startswith(".") for p in d.parents
            )
        ]
        try:
            output_dir = (
                await ListPrompt(
                    _("Where to store the plugin?"), detected + [Choice(_("Other"))]
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ).name
            if output_dir == _("Other"):
                output_dir = await InputPrompt(
                    _("Output Dir:"),
                    validator=lambda x: len(x) > 0 and Path(x).is_dir(),
                    error_message=_("Invalid output dir!"),
                ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()
    elif not Path(output_dir).is_dir():
        click.secho(_("Output dir is not a directory!"), fg="yellow")
        try:
            output_dir = await InputPrompt(
                _("Output Dir:"),
                validator=lambda x: len(x) > 0 and Path(x).is_dir(),
                error_message=_("Invalid output dir!"),
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    create_plugin(name, output_dir, sub_plugin=sub_plugin, template=template)
