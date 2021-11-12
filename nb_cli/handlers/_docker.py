import sys
import logging
from typing import Iterable

import click

try:
    from compose.cli.main import (
        AnsiMode,
        TopLevelCommand,
        DocoptDispatcher,
        perform_command,
        setup_console_handler,
        setup_parallel_logger,
    )

    COMPOSE_INSTALLED = True
except ImportError:
    COMPOSE_INSTALLED = False


def _call_docker_compose(command: str, args: Iterable[str]):
    if not COMPOSE_INSTALLED:
        click.secho(
            "docker-compose not found! install it by using `pip install nb-cli[deploy]`",
            fg="red",
        )
        return
    console_stream = sys.stderr
    console_handler = logging.StreamHandler(console_stream)
    dispatcher = DocoptDispatcher(TopLevelCommand, {"options_first": True})
    options, handler, command_options = dispatcher.parse([command, *args])
    ansi_mode = AnsiMode.AUTO
    setup_console_handler(
        logging.StreamHandler(sys.stderr),
        options.get("--verbose"),
        ansi_mode.use_ansi_codes(console_handler.stream),
        options.get("--log-level"),
    )
    setup_parallel_logger(ansi_mode)
    if ansi_mode is AnsiMode.NEVER:
        command_options["--no-color"] = True
    return perform_command(options, handler, command_options)
