import contextlib
from typing import cast
from pathlib import Path

import click
from noneprompt import Choice, ListPrompt, InputPrompt, ConfirmPrompt, CancelledError

from nb_cli import _
from nb_cli.config import GLOBAL_CONFIG
from nb_cli.cli.utils import find_exact_package, format_package_results
from nb_cli.exceptions import ProcessExecutionError, NoSelectablePackageError
from nb_cli.handlers import (
    EnvironmentExecutor,
    list_plugins,
    create_plugin,
    list_installed_plugins,
)
from nb_cli.cli import (
    CLI_DEFAULT_STYLE,
    ClickAliasedGroup,
    back_,
    exit_,
    run_sync,
    run_async,
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


@plugin.command(help=_("Open nonebot plugin store."))
@run_async
async def store():
    from nb_cli.tui import Gallery

    plugin_store = Gallery()
    plugin_store.datasource = await list_plugins()
    plugin_store.title = _("NB-CLI - NoneBot Plugin Store")
    await plugin_store.run_async()


@plugin.command(
    name="list", help=_("List nonebot plugins published on nonebot homepage.")
)
@click.option(
    "--installed",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to list installed plugins only in current project."),
)
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished plugins."),
)
@run_async
async def list_(installed: bool = False, include_unpublished: bool = False):
    plugins = (
        await list_installed_plugins()
        if installed
        else await list_plugins(include_unpublished=include_unpublished)
    )
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
async def search(name: str | None, include_unpublished: bool = False):
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
    name: str | None,
    pip_args: list[str] | None,
    include_unpublished: bool = False,
):
    extras: str | None = None
    if name and "[" in name:
        name, extras = name.split("[", 1)
        extras = extras.rstrip("]")

    try:
        _installed_plugins = await list_installed_plugins()
        is_installed = False
        plugin = None

        if name is not None and extras is not None:
            with contextlib.suppress(RuntimeError):
                plugin = await find_exact_package(
                    _("Plugin name to install:"),
                    name,
                    _installed_plugins,
                )
                is_installed = True

        if not is_installed:
            _installed = {(p.project_link, p.module_name) for p in _installed_plugins}
            plugin = await find_exact_package(
                _("Plugin name to install:"),
                name,
                [
                    p
                    for p in await list_plugins(include_unpublished=include_unpublished)
                    if (p.project_link, p.module_name) not in _installed
                ],
            )

        assert plugin is not None  # confirmed by above logic
    except CancelledError:
        return
    except NoSelectablePackageError:
        click.echo(_("No available plugin found to install."))
        return

    if include_unpublished:
        click.secho(
            _(
                "WARNING: Unpublished plugins may be installed. "
                "These plugins may be unmaintained or unusable."
            ),
            fg="yellow",
        )

    executor = await EnvironmentExecutor.get()
    try:
        await executor.install(
            plugin.as_requirement(extras=extras, versioned=not no_restrict_version),
            extra_args=pip_args or (),
        )
    except ProcessExecutionError:
        click.secho(
            _(
                "Errors occurred in installing plugin {plugin.name}\n"
                "*** Try `nb plugin install` command with `--no-restrict-version` "
                "option to resolve under loose version constraints may work."
            ).format(plugin=plugin),
            fg="red",
        )
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.add_plugin(plugin)
    except RuntimeError as e:
        click.echo(
            _("Failed to add plugin {plugin.name} to config: {e}").format(
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
    name: str | None,
    pip_args: list[str] | None,
    include_unpublished: bool = False,
):
    try:
        plugin = await find_exact_package(
            _("Plugin name to update:"),
            name,
            await list_installed_plugins(),
        )
    except CancelledError:
        return
    except NoSelectablePackageError:
        click.echo(_("No installed plugin found to update."))
        return

    if include_unpublished:
        click.secho(
            _(
                "WARNING: Unpublished plugins may be installed. "
                "These plugins may be unmaintained or unusable."
            ),
            fg="yellow",
        )

    executor = await EnvironmentExecutor.get()
    try:
        await executor.update(plugin.as_requirement(), extra_args=pip_args or ())
    except ProcessExecutionError:
        click.secho(
            _("Errors occurred in updating plugin {plugin.name}. Aborted.").format(
                plugin=plugin
            ),
            fg="red",
        )
        return


@plugin.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall nonebot plugin from current project."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def uninstall(name: str | None, pip_args: list[str] | None):
    extras: str | None = None
    if name and "[" in name:
        name, extras = name.split("[", 1)
        extras = extras.rstrip("]")

    try:
        plugin = await find_exact_package(
            _("Plugin name to uninstall:"),
            name,
            await list_installed_plugins(),
        )
    except CancelledError:
        return
    except NoSelectablePackageError:
        click.echo(_("No installed plugin found to uninstall."))
        return

    try:
        can_uninstall = GLOBAL_CONFIG.remove_plugin(plugin)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove plugin {plugin.name} from config: {e}").format(
                plugin=plugin, e=e
            )
        )
        return

    if can_uninstall:
        executor = await EnvironmentExecutor.get()
        await executor.uninstall(
            plugin.as_requirement(extras=extras, versioned=False),
            extra_args=pip_args or (),
        )


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
    name: str | None,
    sub_plugin: bool | None,
    output_dir: str | None,
    template: str | None,
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
