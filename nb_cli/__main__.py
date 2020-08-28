#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

import click

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import draw_logo, create_project, handle_no_subcommand


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.version_option(__version__,
                      "-V",
                      "--version",
                      message="%(prog)s: nonebot cli version %(version)s")
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        handle_no_subcommand()


@main.command(aliases=["create", "start"])
def init():
    """Create A NoneBot Project"""
    create_project()


if __name__ == "__main__":
    main()
