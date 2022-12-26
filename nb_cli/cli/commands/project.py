import asyncio
from pathlib import Path
from functools import partial
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
    terminate_project,
    generate_run_script,
    list_project_templates,
    register_signal_handler,
)

TEMPLATE_DESCRIPTION = {
    "bootstrap": "bootstrap (for beginner or user)",
    "simple": "simple (for developer)",
}


async def prompt_common_context() -> Dict[str, Any]:
    click.secho("Loading adapters...")
    all_adapters = await list_adapters()
    click.secho("Loading drivers...")
    all_drivers = await list_drivers()
    click.clear()

    project_name = await InputPrompt(
        "Project Name:", validator=lambda x: len(x.strip()) > 0
    ).prompt_async(style=CLI_DEFAULT_STYLE)

    drivers = [
        choice.data.dict()
        for choice in await CheckboxPrompt(
            "Which driver(s) would you like to use?",
            [
                Choice(f"{driver.name} ({driver.desc})", driver)
                for driver in all_drivers
            ],
            default_select=[
                index
                for index, driver in enumerate(all_drivers)
                if driver.name in DEFAULT_DRIVER
            ],
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    ]

    confirm = False
    adapters = []
    while not confirm:
        adapters = [
            choice.data.dict()
            for choice in await CheckboxPrompt(
                "Which adapter(s) would you like to use?",
                [
                    Choice(f"{adapter.name} ({adapter.desc})", adapter)
                    for adapter in all_adapters
                ],
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        ]
        confirm = (
            True
            if adapters
            else await ConfirmPrompt(
                "You haven't chosen any adapter. Please confirm.",
                default_choice=False,
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        )

    return {"project_name": project_name, "drivers": drivers, "adapters": adapters}


async def prompt_simple_context(context: Dict[str, Any]) -> Dict[str, Any]:
    dir_name = context["project_name"].lower().replace(" ", "-").replace("-", "_")
    src_choices: List[Choice[bool]] = [
        Choice(f'1) In a "{dir_name}" folder', False),
        Choice('2) In a "src" folder', True),
    ]
    context["use_src"] = (
        await ListPrompt("Where to store the plugin?", src_choices).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    ).data

    return context


TEMPLATE_PROMPTS = {
    "simple": prompt_simple_context,
}


@click.command(cls=ClickAliasedCommand, aliases=["init"])
@click.option("-t", "--template", default=None, help="The project template to use.")
@click.pass_context
@run_async
async def create(ctx: click.Context, template: Optional[str]):
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

    try:
        context = await prompt_common_context()
        if inject_prompt := TEMPLATE_PROMPTS.get(template):
            context = await inject_prompt(context)
    except ModuleLoadFailed as e:
        click.secho(repr(e), fg="red")
        ctx.exit()
    except CancelledError:
        ctx.exit()

    create_project(template, {"nonebot": context})

    if not await ConfirmPrompt(
        "Install dependencies now?", default_choice=True
    ).prompt_async(style=CLI_DEFAULT_STYLE):
        ctx.exit()

    project_dir = context["project_name"].replace(" ", "-")
    use_venv = await ConfirmPrompt(
        "Use virtual environment?", default_choice=True
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    # TODO: install dependencies


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
