from pathlib import Path
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
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedCommand
from nb_cli.exceptions import ModuleLoadFailed, NoneBotNotInstalledError
from nb_cli.handlers import (
    run_project,
    list_drivers,
    list_adapters,
    create_project,
    generate_run_script,
    list_builtin_plugins,
    list_project_templates,
)

TEMPLATE_DESCRIPTION = {
    "bootstrap": "bootstrap (for beginner or user)",
    "simple": "simple (for developer)",
}


def prompt_common_context() -> Dict[str, Any]:
    click.secho("Loading adapters...")
    all_adapters = list_adapters()
    click.secho("Loading drivers...")
    all_drivers = list_drivers()
    click.clear()

    project_name = InputPrompt(
        "Project Name:", validator=lambda x: len(x.strip()) > 0
    ).prompt(style=CLI_DEFAULT_STYLE)

    drivers = [
        choice.data.dict()
        for choice in CheckboxPrompt(
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
        ).prompt(style=CLI_DEFAULT_STYLE)
    ]

    confirm = False
    adapters = []
    while not confirm:
        adapters = [
            choice.data.dict()
            for choice in CheckboxPrompt(
                "Which adapter(s) would you like to use?",
                [
                    Choice(f"{adapter.name} ({adapter.desc})", adapter)
                    for adapter in all_adapters
                ],
            ).prompt(style=CLI_DEFAULT_STYLE)
        ]
        confirm = (
            True
            if adapters
            else ConfirmPrompt(
                "You haven't chosen any adapter. Please confirm.",
                default_choice=False,
            ).prompt(style=CLI_DEFAULT_STYLE)
        )

    return {"project_name": project_name, "drivers": drivers, "adapters": adapters}


def prompt_simple_context(context: Dict[str, Any]) -> Dict[str, Any]:
    dir_name = context["project_name"].lower().replace(" ", "-").replace("-", "_")
    src_choices: List[Choice[bool]] = [
        Choice(f'1) In a "{dir_name}" folder', False),
        Choice('2) In a "src" folder', True),
    ]
    context["use_src"] = (
        ListPrompt("Where to store the plugin?", src_choices)
        .prompt(style=CLI_DEFAULT_STYLE)
        .data
    )

    return context


TEMPLATE_PROMPTS = {
    "simple": prompt_simple_context,
}


@click.command(cls=ClickAliasedCommand, aliases=["init"])
@click.option("-t", "--template", default=None, help="The project template to use.")
@click.pass_context
def create(ctx: click.Context, template: Optional[str]):
    """Create a NoneBot project."""
    if not template:
        templates = list_project_templates()
        try:
            template = (
                ListPrompt(
                    "Select a template to use",
                    [Choice(TEMPLATE_DESCRIPTION.get(t, t), t) for t in templates],
                )
                .prompt(style=CLI_DEFAULT_STYLE)
                .data
            )
        except CancelledError:
            ctx.exit()

    try:
        context = prompt_common_context()
        if inject_prompt := TEMPLATE_PROMPTS.get(template):
            context = inject_prompt(context)
    except ModuleLoadFailed as e:
        click.secho(repr(e), fg="red")
        ctx.exit()
    except CancelledError:
        ctx.exit()

    create_project(template, {"nonebot": context})

    if not ConfirmPrompt("Install dependencies now?", default_choice=True).prompt(
        style=CLI_DEFAULT_STYLE
    ):
        ctx.exit()

    project_dir = context["project_name"].replace(" ", "-")
    use_venv = ConfirmPrompt("Use virtual environment?", default_choice=True).prompt(
        style=CLI_DEFAULT_STYLE
    )
    # TODO: install dependencies


@click.command(cls=ClickAliasedCommand)
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="The file script saved to.",
)
def generate(file: str):
    """Generate entry file of your bot."""
    content = generate_run_script()
    Path(file).write_text(content)


@click.command(cls=ClickAliasedCommand, aliases=["start"])
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="Exist entry file of your bot.",
)
def run(file: str):
    """Run the bot in current folder."""
    run_project(exist_bot=Path(file))
