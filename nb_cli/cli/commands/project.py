import re
import sys
import asyncio
from pathlib import Path
from functools import partial
from dataclasses import field, dataclass
from typing import Any, Dict, List, Optional

import click
from noneprompt import (
    Choice,
    ListPrompt,
    InputPrompt,
    ConfirmPrompt,
    CancelledError,
    CheckboxPrompt,
)

from nb_cli import _
from nb_cli.config import ConfigManager
from nb_cli.exceptions import ModuleLoadFailed
from nb_cli.consts import WINDOWS, DEFAULT_DRIVER
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedCommand, run_async
from nb_cli.handlers import (
    Reloader,
    FileFilter,
    run_project,
    list_drivers,
    list_adapters,
    create_project,
    call_pip_install,
    create_virtualenv,
    detect_virtualenv,
    terminate_process,
    generate_run_script,
    list_builtin_plugins,
    remove_signal_handler,
    list_project_templates,
    register_signal_handler,
)

VALID_PROJECT_NAME = r"^[a-zA-Z][a-zA-Z0-9 _-]*$"
BLACKLISTED_PROJECT_NAME = {"nonebot", "bot"}
TEMPLATE_DESCRIPTION = {
    "bootstrap": _("bootstrap (for beginner or user)"),
    "simple": _("simple (for developer)"),
}

if sys.version_info >= (3, 10):
    BLACKLISTED_PROJECT_NAME.update(sys.stdlib_module_names)


@dataclass
class ProjectContext:
    variables: Dict[str, Any] = field(default_factory=dict)
    packages: List[str] = field(default_factory=list)


def project_name_validator(name: str) -> bool:
    return (
        bool(re.match(VALID_PROJECT_NAME, name))
        and name not in BLACKLISTED_PROJECT_NAME
    )


async def prompt_common_context(context: ProjectContext) -> ProjectContext:
    click.secho(_("Loading adapters..."))
    all_adapters = await list_adapters()
    click.secho(_("Loading drivers..."))
    all_drivers = await list_drivers()
    click.clear()

    project_name = await InputPrompt(
        _("Project Name:"), validator=project_name_validator
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["project_name"] = project_name

    drivers = await CheckboxPrompt(
        _("Which driver(s) would you like to use?"),
        [Choice(f"{driver.name} ({driver.desc})", driver) for driver in all_drivers],
        default_select=[
            index
            for index, driver in enumerate(all_drivers)
            if driver.name in DEFAULT_DRIVER
        ],
        validator=bool,
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["drivers"] = [d.data.dict() for d in drivers]
    context.packages.extend(
        [d.data.project_link for d in drivers if d.data.project_link]
    )

    confirm = False
    adapters = []
    while not confirm:
        adapters = await CheckboxPrompt(
            _("Which adapter(s) would you like to use?"),
            [
                Choice(f"{adapter.name} ({adapter.desc})", adapter)
                for adapter in all_adapters
            ],
        ).prompt_async(style=CLI_DEFAULT_STYLE)
        confirm = (
            True
            if adapters
            else await ConfirmPrompt(
                _("You haven't chosen any adapter! Please confirm."),
                default_choice=False,
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        )

    context.variables["adapters"] = [a.data.dict() for a in adapters]
    context.packages.extend([a.data.project_link for a in adapters])

    return context


async def prompt_simple_context(context: ProjectContext) -> ProjectContext:
    dir_name = (
        context.variables["project_name"].lower().replace(" ", "-").replace("-", "_")
    )
    src_choices: List[Choice[bool]] = [
        Choice(_('1) In a "{dir_name}" folder').format(dir_name=dir_name), False),
        Choice(_('2) In a "src" folder'), True),
    ]
    context.variables["use_src"] = (
        await ListPrompt(_("Where to store the plugin?"), src_choices).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    ).data

    return context


TEMPLATE_PROMPTS = {
    "simple": prompt_simple_context,
}


@click.command(
    cls=ClickAliasedCommand,
    aliases=["init"],
    context_settings={"ignore_unknown_options": True},
    help=_("Create a NoneBot project."),
)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help=_("The project template to use."))
@click.option(
    "-p",
    "--python-interpreter",
    default=None,
    help=_("The python interpreter virtualenv is installed into."),
)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    output_dir: Optional[str],
    template: Optional[str],
    python_interpreter: Optional[str],
    pip_args: Optional[List[str]],
):
    if not template:
        templates = list_project_templates()
        try:
            template = (
                await ListPrompt(
                    _("Select a template to use:"),
                    [Choice(TEMPLATE_DESCRIPTION.get(t, t), t) for t in templates],
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ).data
        except CancelledError:
            ctx.exit()

    context = ProjectContext()
    try:
        context = await prompt_common_context(context)
        if inject_prompt := TEMPLATE_PROMPTS.get(template):
            context = await inject_prompt(context)
    except ModuleLoadFailed as e:
        click.secho(repr(e), fg="red")
        ctx.exit()
    except CancelledError:
        ctx.exit()

    create_project(template, {"nonebot": context.variables}, output_dir)

    try:
        install_dependencies = await ConfirmPrompt(
            _("Install dependencies now?"), default_choice=True
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    use_venv = False
    project_dir_name = context.variables["project_name"].replace(" ", "-")
    project_dir = Path(output_dir or ".") / project_dir_name
    venv_dir = project_dir / ".venv"

    if install_dependencies:
        try:
            use_venv = await ConfirmPrompt(
                _("Create virtual environment?"), default_choice=True
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

        path = None
        if use_venv:
            click.secho(
                _("Creating virtual environment in {venv_dir} ...").format(
                    venv_dir=venv_dir
                ),
                fg="yellow",
            )
            await create_virtualenv(
                venv_dir, prompt=project_dir_name, python_path=python_interpreter
            )
            path = (
                venv_dir
                / ("Scripts" if WINDOWS else "bin")
                / ("python.exe" if WINDOWS else "python")
            )

        proc = await call_pip_install(
            ["nonebot2", *context.packages], pip_args, python_path=path
        )
        await proc.wait()

        builtin_plugins = await list_builtin_plugins(python_path=path)
        try:
            loaded_builtin_plugins = [
                c.data
                for c in await CheckboxPrompt(
                    _("Which builtin plugin(s) would you like to use?"),
                    [Choice(p, p) for p in builtin_plugins],
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ]
        except CancelledError:
            ctx.exit()

        try:
            m = ConfigManager(python=path, config_file=project_dir / "pyproject.toml")
            for plugin in loaded_builtin_plugins:
                m.add_builtin_plugin(plugin)
        except Exception as e:
            click.secho(
                _(
                    "Failed to add builtin plugins {builtin_plugins} to config: {e}"
                ).format(builtin_plugin=loaded_builtin_plugins, e=e),
                fg="red",
            )
            ctx.exit()

    click.secho(_("Done!"), fg="green")
    click.secho(
        _(
            "Add following packages to your project using dependency manager like poetry or pdm:"
        ),
        fg="green",
    )
    click.secho(f"  {' '.join(context.packages)}", fg="green")
    click.secho(_("Run the following command to start your bot:"), fg="green")
    click.secho(f"  cd {project_dir}", fg="green")
    click.secho("  nb run --reload", fg="green")


@click.command(cls=ClickAliasedCommand, help=_("Generate entry file of your bot."))
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help=_("The file script saved to."),
)
@run_async
async def generate(file: str):
    content = await generate_run_script()
    Path(file).write_text(content)


@click.command(
    cls=ClickAliasedCommand, aliases=["start"], help=_("Run the bot in current folder.")
)
@click.option("-d", "--cwd", default=".", help=_("The working directory."))
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help=_("Exist entry file of your bot."),
)
@click.option(
    "--venv/--no-venv",
    default=True,
    help=_("Auto detect virtual environment."),
    show_default=True,
)
@click.option(
    "-r",
    "--reload",
    is_flag=True,
    default=False,
    help=_("Reload the bot when file changed."),
)
@click.option(
    "--reload-includes",
    multiple=True,
    default=None,
    help=_("Files to watch for changes."),
)
@click.option(
    "--reload-excludes",
    multiple=True,
    default=None,
    help=_("Files to ignore for changes."),
)
@run_async
async def run(
    cwd: str,
    file: str,
    venv: bool,
    reload: bool,
    reload_includes: Optional[List[str]],
    reload_excludes: Optional[List[str]],
):
    if python_path := detect_virtualenv(Path(cwd)) if venv else None:
        click.secho(
            _("Using virtual environment: {python_path}").format(
                python_path=python_path
            ),
            fg="green",
        )

    if reload:
        await Reloader(
            partial(run_project, exist_bot=Path(file), python_path=python_path),
            terminate_process,
            file_filter=FileFilter(reload_includes, reload_excludes),
            cwd=Path(cwd),
        ).run()
    else:
        should_exit = asyncio.Event()

        def shutdown(signum, frame):
            should_exit.set()

        register_signal_handler(shutdown)

        async def wait_for_exit():
            await should_exit.wait()
            await terminate_process(proc)

        proc = await run_project(
            exist_bot=Path(file), python_path=python_path, cwd=Path(cwd)
        )
        task = asyncio.create_task(wait_for_exit())
        await proc.wait()
        should_exit.set()
        await task
        remove_signal_handler(shutdown)
