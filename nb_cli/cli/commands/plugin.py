from pathlib import Path
from typing import Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, ConfirmPrompt, CancelledError

from nb_cli import _
from nb_cli.config import GLOBAL_CONFIG
from nb_cli.cli.utils import find_exact_package
from nb_cli.cli import (
    CLI_DEFAULT_STYLE,
    ClickAliasedGroup,
    back_,
    exit_,
    run_sync,
    run_async,
)
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


@plugin.command(
    name="list", help=_("List nonebot plugins published on nonebot homepage.")
)
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished plugins."),
)
@run_async
async def list_(include_unpublished: bool = False):
    plugins = await list_plugins(include_unpublished=include_unpublished)
    if include_unpublished:
        click.secho(_("WARNING: Unpublished plugins may be included."), fg="yellow")
    click.echo(format_package_results(plugins))


@plugin.command(help=_("Search for nonebot plugins published on nonebot homepage."))
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished plugins."),
)
@click.argument("name", nargs=1, required=False, default=None)
@run_async
async def search(name: Optional[str], include_unpublished: bool = False):
    if name is None:
        name = await InputPrompt(_("Plugin name to search:")).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    plugins = await list_plugins(name, include_unpublished=include_unpublished)
    if include_unpublished:
        click.secho(_("WARNING: Unpublished plugins may be included."), fg="yellow")
    click.echo(format_package_results(plugins))


@plugin.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install nonebot plugin to current project."),
)
@click.option(
    "--no-restrict-version", nargs=1, is_flag=True, flag_value=True, default=False
)
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished plugins."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(
    ctx: click.Context,
    no_restrict_version: bool,
    name: Optional[str],
    pip_args: Optional[list[str]],
    include_unpublished: bool = False,
):
    try:
        plugin = await find_exact_package(
            _("Plugin name to install:"),
            name,
            await list_plugins(include_unpublished=include_unpublished),
        )
    except CancelledError:
        return

    if include_unpublished:
        click.secho(
            _(
                "WARNING: Unpublished plugins may be installed. "
                "These plugins may be unmaintained or unusable."
            ),
            fg="yellow",
        )

    try:
        GLOBAL_CONFIG.add_plugin(plugin)
    except RuntimeError as e:
        click.echo(
            _("Failed to add plugin {plugin.name} to config: {e}").format(
                plugin=plugin, e=e
            )
        )

    pkg = (
        plugin.project_link
        if no_restrict_version
        else f"{plugin.project_link}>={plugin.version}"
    )
    proc = await call_pip_install(pkg, pip_args)
    if await proc.wait() != 0:
        click.secho(
            _(
                "Errors occurred in installing plugin {plugin.name}\n"
                "*** Try `nb plugin install` command with `--no-restrict-version` "
                "option to resolve under loose version constraints may work."
            ).format(plugin=plugin),
            fg="red",
        )
        assert proc.returncode
        ctx.exit(proc.returncode)

    try:
        GLOBAL_CONFIG.add_dependency(plugin)
    except RuntimeError as e:
        click.echo(
            _("Failed to add plugin {plugin.name} to dependencies: {e}").format(
                plugin=plugin, e=e
            )
        )


@plugin.command(
    context_settings={"ignore_unknown_options": True}, help=_("Update nonebot plugin.")
)
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished plugins."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def update(
    name: Optional[str],
    pip_args: Optional[list[str]],
    include_unpublished: bool = False,
):
    try:
        plugin = await find_exact_package(
            _("Plugin name to update:"),
            name,
            await list_plugins(include_unpublished=include_unpublished),
        )
    except CancelledError:
        return

    if include_unpublished:
        click.secho(
            _(
                "WARNING: Unpublished plugins may be installed. "
                "These plugins may be unmaintained or unusable."
            ),
            fg="yellow",
        )

    proc = await call_pip_update(plugin.project_link, pip_args)
    if await proc.wait() != 0:
        click.secho(
            _("Errors occurred in updating plugin {plugin.name}. Aborted.").format(
                plugin=plugin
            ),
            fg="red",
        )
        return

    try:
        GLOBAL_CONFIG.update_dependency(plugin)
    except RuntimeError as e:
        click.echo(
            _("Failed to update plugin {plugin.name} to dependencies: {e}").format(
                plugin=plugin, e=e
            )
        )


@plugin.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall nonebot plugin from current project."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def uninstall(name: Optional[str], pip_args: Optional[list[str]]):
    try:
        plugin = await find_exact_package(
            _("Plugin name to uninstall:"),
            name,
            await list_plugins(
                include_unpublished=True  # unpublished modules are always removable
            ),
        )
    except CancelledError:
        return

    try:
        can_uninstall = GLOBAL_CONFIG.remove_plugin(plugin)
        if can_uninstall:
            GLOBAL_CONFIG.remove_dependency(plugin)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove plugin {plugin.name} from config: {e}").format(
                plugin=plugin, e=e
            )
        )
        return

    if can_uninstall:
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
            return
    if sub_plugin is None:
        try:
            sub_plugin = await ConfirmPrompt(
                _("Use nested plugin?"), default_choice=False
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            return

    if output_dir is None:
        detected: list[Choice[None]] = [
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
                    _("Where to store the plugin?"),
                    [*detected, Choice[None](_("Other"))],
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ).name
            if output_dir == _("Other"):
                output_dir = await InputPrompt(
                    _("Output Dir:"),
                    validator=lambda x: len(x) > 0 and Path(x).is_dir(),
                    error_message=_("Invalid output dir!"),
                ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            return
    elif not Path(output_dir).is_dir():
        click.secho(_("Output dir is not a directory!"), fg="yellow")
        try:
            output_dir = await InputPrompt(
                _("Output Dir:"),
                validator=lambda x: len(x) > 0 and Path(x).is_dir(),
                error_message=_("Invalid output dir!"),
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            return

    create_plugin(name, output_dir, sub_plugin=sub_plugin, template=template)
    ctx.exit()
