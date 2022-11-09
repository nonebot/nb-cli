import sys
from pathlib import Path

import click
import pkg_resources

from nb_cli.commands.self import self
from nb_cli.config import ConfigManager
from nb_cli.commands.config import config
from nb_cli.commands.driver import driver
from nb_cli.commands.plugin import plugin
from nb_cli.commands.adapter import adapter
from nb_cli.handlers import handle_no_subcommand
from nb_cli.commands.main import run, init, generate
from nb_cli.commands.deploy import exit, build, deploy
from nb_cli.utils import ClickAliasedGroup, script_wrapper

sys.path.insert(0, ".")

try:
    _dist = pkg_resources.get_distribution("nb-cli")
    __version__ = _dist.version
    VERSION = _dist.parsed_version
except pkg_resources.DistributionNotFound:
    __version__ = None
    VERSION = None


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.version_option(
    __version__,
    "-V",
    "--version",
    message="%(prog)s: nonebot cli version %(version)s",
)
@click.pass_context
def main(ctx: click.Context):
    if ctx.invoked_subcommand is None:
        handle_no_subcommand()


main.add_command(init)
main.add_command(generate)
main.add_command(run)

main.add_command(config)
main.add_command(build)
main.add_command(deploy)
main.add_command(exit)

main.add_command(adapter)
main.add_command(plugin)
main.add_command(driver)
main.add_command(self)

if ConfigManager.LOCAL_CONFIG_PATH.exists():
    local_config = ConfigManager.get_local_config()
    scripts = local_config.get_scripts()

    for name, command in scripts.items():
        if name not in main.commands:
            main.add_command(script_wrapper(command), name)
        else:
            raise ValueError(
                f'The command "{name}" in local config has been already registered!'
            )

    from nb_cli.plugin import load_from_toml

    load_from_toml("pyproject.toml")

if __name__ == "__main__":
    main()
