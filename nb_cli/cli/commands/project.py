from pathlib import Path
from typing import Optional

import click
from noneprompt import Choice, ListPrompt, InputPrompt, CancelledError

from nb_cli.config import Config
from nb_cli.consts import CONFIG_KEY
from nb_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedCommand
from nb_cli.handlers import (
    run_project,
    create_project,
    generate_run_script,
    list_project_templates,
)

TEMPLATE_DESCRIPTION = {
    "bootstrap": "bootstrap (for beginner or user)",
    "simple": "simple (for developer)",
}


@click.command(cls=ClickAliasedCommand, aliases=["init"])
@click.option(
    "-t", "--template", default=None, help="The project template to use"
)
@click.pass_context
def create(ctx: click.Context, template: Optional[str]):
    """Create a NoneBot project."""
    if not template:
        templates = list_project_templates()
        try:
            template = (
                ListPrompt(
                    "Select a template to use",
                    [
                        Choice(TEMPLATE_DESCRIPTION.get(t, t), t)
                        for t in templates
                    ],
                )
                .prompt(style=CLI_DEFAULT_STYLE)
                .data
            )
        except CancelledError:
            ctx.exit()

    try:
        project_name = InputPrompt(
            "Project Name:", validator=lambda x: len(x) > 0
        ).prompt(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    create_project(template, {"project_name": project_name})


@click.command(cls=ClickAliasedCommand)
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="The file script saved to",
)
@click.pass_context
def generate(ctx: click.Context, file: str):
    """Generate entry file of your bot."""
    config: Config = ctx.meta[CONFIG_KEY]
    content = generate_run_script(
        config.nonebot.adapters, config.nonebot.builtin_plugins
    )
    Path(file).write_text(content)


@click.command(cls=ClickAliasedCommand, aliases=["start"])
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help="Exist entry file of your bot",
)
@click.pass_context
def run(ctx: click.Context, file: str):
    """Run the bot in current folder."""
    config: Config = ctx.meta[CONFIG_KEY]
    run_project(
        adapters=config.nonebot.adapters,
        builtin_plugins=config.nonebot.builtin_plugins,
        exist_bot=Path(file),
        python_path=config.nb_cli.python,
    )
