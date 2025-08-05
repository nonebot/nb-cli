from pathlib import Path
from typing import Optional, cast

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

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
    list_adapters,
    create_adapter,
    call_pip_update,
    call_pip_install,
    call_pip_uninstall,
    format_package_results,
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


@adapter.command(
    name="list", help=_("List nonebot adapters published on nonebot homepage.")
)
@run_async
async def list_():
    adapters = await list_adapters()
    click.echo(format_package_results(adapters))


@adapter.command(help=_("Search for nonebot adapters published on nonebot homepage."))
@click.argument("name", nargs=1, default=None)
@run_async
async def search(name: Optional[str]):
    if name is None:
        name = await InputPrompt(_("Adapter name to search:")).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    adapters = await list_adapters(name)
    click.echo(format_package_results(adapters))


@adapter.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install nonebot adapter to current project."),
)
@click.option(
    "--no-restrict-version", nargs=1, is_flag=True, flag_value=True, default=False
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(
    ctx: click.Context,
    no_restrict_version: bool,
    name: Optional[str],
    pip_args: Optional[list[str]],
):
    try:
        adapter = await find_exact_package(
            _("Adapter name to install:"), name, await list_adapters()
        )
    except CancelledError:
        return

    try:
        GLOBAL_CONFIG.add_adapter(adapter)
    except RuntimeError as e:
        click.echo(
            _("Failed to add adapter {adapter.name} to config: {e}").format(
                adapter=adapter, e=e
            )
        )

    pkg = (
        adapter.project_link
        if no_restrict_version
        else f"{adapter.project_link}>={adapter.version}"
    )
    proc = await call_pip_install(pkg, pip_args)
    if await proc.wait() != 0:
        click.secho(
            _(
                "Errors occurred in installing adapter {adapter.name}\n"
                "    *** Try `nb adapter install` command with `--no-restrict-version` "
                "option to resolve under loose version constraints may work."
            ).format(adapter=adapter),
            fg="red",
        )
        assert proc.returncode
        ctx.exit(proc.returncode)

    try:
        GLOBAL_CONFIG.add_dependency(adapter)
    except RuntimeError as e:
        click.echo(
            _("Failed to add adapter {adapter.name} to dependencies: {e}").format(
                adapter=adapter, e=e
            )
        )


@adapter.command(
    context_settings={"ignore_unknown_options": True}, help=_("Update nonebot adapter.")
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def update(name: Optional[str], pip_args: Optional[list[str]]):
    try:
        adapter = await find_exact_package(
            _("Adapter name to update:"), name, await list_adapters()
        )
    except CancelledError:
        return

    proc = await call_pip_update(adapter.project_link, pip_args)
    await proc.wait()

    try:
        GLOBAL_CONFIG.update_dependency(adapter)
    except RuntimeError as e:
        click.echo(
            _("Failed to update adapter {adapter.name} to dependencies: {e}").format(
                adapter=adapter, e=e
            )
        )


@adapter.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall nonebot adapter from current project."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@run_async
async def uninstall(name: Optional[str], pip_args: Optional[list[str]]):
    try:
        adapter = await find_exact_package(
            _("Adapter name to uninstall:"), name, await list_adapters()
        )
    except CancelledError:
        return

    try:
        can_uninstall = GLOBAL_CONFIG.remove_adapter(adapter)
        if can_uninstall:
            GLOBAL_CONFIG.remove_dependency(adapter)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove adapter {adapter.name} from config: {e}").format(
                adapter=adapter, e=e
            )
        )
        return

    if can_uninstall:
        proc = await call_pip_uninstall(adapter.project_link, pip_args)
        await proc.wait()


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
    name: Optional[str],
    output_dir: Optional[str],
    template: Optional[str],
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
