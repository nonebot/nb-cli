import logging

import click

SUCCESS = 25


class Logger(logging.Logger):
    def success(self, msg, *args, **kwargs):
        if self.isEnabledFor(SUCCESS):
            self._log(SUCCESS, msg, args, **kwargs)


class ClickHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = record.getMessage()
        if record.levelno >= logging.ERROR:
            click.secho(msg, fg="red")
        elif record.levelno >= logging.WARNING:
            click.secho(msg, fg="yellow")
        elif record.levelno >= SUCCESS:
            click.secho(msg, fg="green")
        else:
            click.echo(msg)
