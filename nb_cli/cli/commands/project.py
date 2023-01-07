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

from nb_cli.consts import DEFAULT_DRIVER
from nb_cli.exceptions import ModuleLoadFailed
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedCommand, run_async
from nb_cli.handlers import (
    Reloader,
    FileFilter,
    run_project,
    list_drivers,
    list_adapters,
    create_project,
    call_pip_install,
    terminate_project,
    generate_run_script,
    remove_signal_handler,
    list_project_templates,
    register_signal_handler,
)

VALID_PROJECT_NAME = r"^[a-zA-Z][a-zA-Z0-9 _-]*$"
BLACKLISTED_PROJECT_NAME = {"nonebot", "bot"}
TEMPLATE_DESCRIPTION = {
    "bootstrap": "bootstrap (for beginner or user)",
    "simple": "simple (for developer)",
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
    click.secho("Loading adapters...")
    all_adapters = await list_adapters()
    click.secho("Loading drivers...")
    all_drivers = await list_drivers()
    click.clear()

    project_name = await InputPrompt(
        "Project Name:", validator=project_name_validator
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["project_name"] = project_name

    drivers = await CheckboxPrompt(
        "Which driver(s) would you like to use?",
        [Choice(f"{driver.name} ({driver.desc})", driver) for driver in all_drivers],
        default_select=[
            index
            for index, driver in enumerate(all_drivers)
            if driver.name in DEFAULT_DRIVER
        ],
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["drivers"] = [d.data.dict() for d in drivers]
    context.packages.extend([d.data.project_link for d in drivers])

    confirm = False
    adapters = []
    while not confirm:
        adapters = await CheckboxPrompt(
            "Which adapter(s) would you like to use?",
            [
                Choice(f"{adapter.name} ({adapter.desc})", adapter)
                for adapter in all_adapters
            ],
        ).prompt_async(style=CLI_DEFAULT_STYLE)
        confirm = (
            True
            if adapters
            else await ConfirmPrompt(
                "You haven't chosen any adapter. Please confirm.",
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
        Choice(f'1) In a "{dir_name}" folder', False),
        Choice('2) In a "src" folder', True),
    ]
    context.variables["use_src"] = (
        await ListPrompt("Where to store the plugin?", src_choices).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    ).data

    return context


TEMPLATE_PROMPTS = {
    "simple": prompt_simple_context,
}


@click.command(cls=ClickAliasedCommand, aliases=["init"])
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help="The project template to use.")
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    output_dir: Optional[str],
    template: Optional[str],
    pip_args: Optional[List[str]],
):
    """Create a NoneBot project."""
    if not template:
        templates = list_project_templates()
        try:
            template = (
                await ListPrompt(
                    "Select a template to use",
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
        if not await ConfirmPrompt(
            "Install dependencies now?", default_choice=True
        ).prompt_async(style=CLI_DEFAULT_STYLE):
            ctx.exit()
    except CancelledError:
        ctx.exit()

    project_dir = context.variables["project_name"].replace(" ", "-")
    venv_dir = Path(output_dir or ".") / project_dir / ".venv"
    try:
        use_venv = await ConfirmPrompt(
            "Use virtual environment?", default_choice=True
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    await call_pip_install(context.packages, pip_args)


@click.command(cls=ClickAliasedCommand)
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="The file script saved to.",
)
@run_async
async def generate(file: str):
    """Generate entry file of your bot."""
    content = await generate_run_script()
    Path(file).write_text(content)


@click.command(cls=ClickAliasedCommand, aliases=["start"])
@click.option("-d", "--cwd", default=".", help="The working directory.")
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="Exist entry file of your bot.",
)
@click.option(
    "-r",
    "--reload",
    is_flag=True,
    default=False,
    help="Reload the bot when file changed.",
)
@click.option(
    "--reload-includes", multiple=True, default=None, help="Files to watch for changes."
)
@click.option(
    "--reload-excludes",
    multiple=True,
    default=None,
    help="Files to ignore for changes.",
)
@run_async
async def run(
    cwd: str,
    file: str,
    reload: bool,
    reload_includes: Optional[List[str]],
    reload_excludes: Optional[List[str]],
):
    """Run the bot in current folder."""
    if reload:
        await Reloader(
            partial(run_project, exist_bot=Path(file)),
            terminate_project,
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
            await terminate_project(proc)

        proc = await run_project(exist_bot=Path(file), cwd=Path(cwd))
        task = asyncio.create_task(wait_for_exit())
        await proc.wait()
        should_exit.set()
        await task
        remove_signal_handler(shutdown)
