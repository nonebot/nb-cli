import contextlib
from typing import cast
from pathlib import Path

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

from nb_cli import _
from nb_cli.config import GLOBAL_CONFIG
from nb_cli.cli.utils import find_exact_package, format_package_results
from nb_cli.exceptions import ProcessExecutionError, NoSelectablePackageError
from nb_cli.cli import (
    CLI_DEFAULT_STYLE,
    ClickAliasedGroup,
    back_,
    exit_,
    run_sync,
    run_async,
)
from nb_cli.handlers import (
    EnvironmentExecutor,
    list_adapters,
    create_adapter,
    list_installed_adapters,
)


@click.group(
    cls=ClickAliasedGroup, invoke_without_command=True, help=_("Manage bot adapters.")
)
@click.pass_context
@run_async
async def adapter(ctx: click.Context):
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


@adapter.command(help=_("Open nonebot adapter store."))
@run_async
async def store():
    from nb_cli.tui import Gallery

    adapter_store = Gallery()
    adapter_store.datasource = await list_adapters()
    adapter_store.title = _("NB-CLI - NoneBot Adapter Store")
    await adapter_store.run_async()


@adapter.command(
    name="list", help=_("List nonebot adapters published on nonebot homepage.")
)
@click.option(
    "--installed",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to list installed adapters only in current project."),
)
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished adapters."),
)
@run_async
async def list_(installed: bool = False, include_unpublished: bool = False):
    adapters = (
        await list_installed_adapters()
        if installed
        else await list_adapters(include_unpublished=include_unpublished)
    )
    if include_unpublished:
        click.secho(_("WARNING: Unpublished adapters may be included."), fg="yellow")
    click.echo(format_package_results(adapters))


@adapter.command(help=_("Search for nonebot adapters published on nonebot homepage."))
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished adapters."),
)
@click.argument("name", nargs=1, default=None)
@run_async
async def search(name: str | None, include_unpublished: bool = False):
    if name is None:
        name = await InputPrompt(_("Adapter name to search:")).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    adapters = await list_adapters(name, include_unpublished=include_unpublished)
    if include_unpublished:
        click.secho(_("WARNING: Unpublished adapters may be included."), fg="yellow")
    click.echo(format_package_results(adapters))


@adapter.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install nonebot adapter to current project."),
)
@click.option(
    "--no-restrict-version", nargs=1, is_flag=True, flag_value=True, default=False
)
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished adapters."),
)
@click.argument("name", nargs=1, default=None)
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
        _installed_adapters = await list_installed_adapters()
        is_installed = False
        adapter = None

        if name is not None and extras is not None:
            with contextlib.suppress(RuntimeError):
                adapter = await find_exact_package(
                    _("Adapter name to install:"),
                    name,
                    _installed_adapters,
                )
                is_installed = True

        if not is_installed:
            _installed = {(a.project_link, a.module_name) for a in _installed_adapters}
            adapter = await find_exact_package(
                _("Adapter name to install:"),
                name,
                [
                    a
                    for a in await list_adapters(
                        include_unpublished=include_unpublished
                    )
                    if (a.project_link, a.module_name) not in _installed
                ],
            )

        assert adapter is not None  # confirmed by above logic
    except CancelledError:
        return
    except NoSelectablePackageError:
        click.echo(_("No available adapter found to install."))
        return

    if include_unpublished:
        click.secho(
            _(
                "WARNING: Unpublished adapters may be installed. "
                "These adapters may be unmaintained or unusable."
            ),
            fg="yellow",
        )

    executor = await EnvironmentExecutor.get()
    try:
        await executor.install(
            adapter.as_requirement(extras=extras, versioned=not no_restrict_version),
            extra_args=pip_args or (),
        )
    except ProcessExecutionError:
        click.secho(
            _(
                "Errors occurred in installing adapter {adapter.name}\n"
                "*** Try `nb adapter install` command with `--no-restrict-version` "
                "option to resolve under loose version constraints may work."
            ).format(adapter=adapter),
            fg="red",
        )
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.add_adapter(adapter)
    except RuntimeError as e:
        click.echo(
            _("Failed to add adapter {adapter.name} to config: {e}").format(
                adapter=adapter, e=e
            )
        )


@adapter.command(
    context_settings={"ignore_unknown_options": True}, help=_("Update nonebot adapter.")
)
@click.option(
    "--include-unpublished",
    is_flag=True,
    default=False,
    flag_value=True,
    help=_("Whether to include unpublished adapters."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def update(
    name: str | None,
    pip_args: list[str] | None,
    include_unpublished: bool = False,
):
    try:
        adapter = await find_exact_package(
            _("Adapter name to update:"),
            name,
            await list_installed_adapters(),
        )
    except CancelledError:
        return
    except NoSelectablePackageError:
        click.echo(_("No installed adapter found to update."))
        return

    if include_unpublished:
        click.secho(
            _(
                "WARNING: Unpublished adapters may be installed. "
                "These adapters may be unmaintained or unusable."
            ),
            fg="yellow",
        )

    executor = await EnvironmentExecutor.get()
    try:
        await executor.install(
            adapter.as_requirement(versioned=False),
            extra_args=pip_args or (),
        )
    except ProcessExecutionError:
        click.secho(
            _("Errors occurred in updating adapter {adapter.name}. Aborted.").format(
                adapter=adapter
            ),
            fg="red",
        )
        return


@adapter.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall nonebot adapter from current project."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def uninstall(name: str | None, pip_args: list[str] | None):
    extras: str | None = None
    if name and "[" in name:
        name, extras = name.split("[", 1)
        extras = extras.rstrip("]")

    try:
        adapter = await find_exact_package(
            _("Adapter name to uninstall:"),
            name,
            await list_installed_adapters(),
        )
    except CancelledError:
        return
    except NoSelectablePackageError:
        click.echo(_("No installed adapter found to uninstall."))
        return

    try:
        can_uninstall = GLOBAL_CONFIG.remove_adapter(adapter)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove adapter {adapter.name} from config: {e}").format(
                adapter=adapter, e=e
            )
        )
        return

    if can_uninstall:
        executor = await EnvironmentExecutor.get()
        await executor.uninstall(
            adapter.as_requirement(extras=extras, versioned=False),
            extra_args=pip_args or (),
        )


@adapter.command(aliases=["new"], help=_("Create a new nonebot adapter."))
@click.argument("name", default=None)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help=_("The adapter template to use."))
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    name: str | None,
    output_dir: str | None,
    template: str | None,
):
    if name is None:
        try:
            name = await InputPrompt(_("Adapter name:")).prompt_async(
                style=CLI_DEFAULT_STYLE
            )
        except CancelledError:
            return
    if output_dir is None:
        detected: list[Choice[None]] = [
            Choice(str(x))
            for x in Path(".").glob("**/adapters/")
            if x.is_dir()
            and not any(
                p.name.startswith(".") or p.name.startswith("_") for p in x.parents
            )
        ] or [
            Choice(f"{x}/adapters/")
            for x in Path(".").glob("*/")
            if x.is_dir() and not x.name.startswith(".") and not x.name.startswith("_")
        ]
        try:
            output_dir = (
                await ListPrompt(
                    _("Where to store the adapter?"),
                    [*detected, Choice[None](_("Other"))],
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ).name
            if output_dir == _("Other"):
                output_dir = await InputPrompt(
                    _("Output Dir:"),
                    validator=lambda x: len(x) > 0 and Path(x).is_dir(),
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
    create_adapter(name, output_dir, template=template)
    ctx.exit()
