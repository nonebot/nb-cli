#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "0.1.0"

import sys
import click

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import run_bot, create_project, handle_no_subcommand

sys.path.insert(0, ".")


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.version_option(__version__,
                      "-V",
                      "--version",
                      message="%(prog)s: nonebot cli version %(version)s")
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        handle_no_subcommand()


@main.command(aliases=["create"])
def init():
    """Create A NoneBot Project"""
    create_project()


@main.command(aliases=["start"])
def run():
    """Run the Bot in Current Folder"""
    run_bot()


if __name__ == "__main__":
    main()
