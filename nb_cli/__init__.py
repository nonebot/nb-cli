import sys
import click
import pkg_resources

from nb_cli.commands.main import init, run
from nb_cli.commands.deploy import build, deploy, exit
from nb_cli.commands.adapter import adapter
from nb_cli.commands.plugin import plugin

from nb_cli.utils import ClickAliasedGroup
from nb_cli.handlers import handle_no_subcommand

sys.path.insert(0, ".")

try:
    _dist = pkg_resources.get_distribution("nb-cli")
    __version__ = _dist.version
    VERSION = _dist.parsed_version
except pkg_resources.DistributionNotFound:
    __version__ = None
    VERSION = None


@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.version_option(__version__,
                      "-V",
                      "--version",
                      message="%(prog)s: nonebot cli version %(version)s")
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        handle_no_subcommand()


main.add_command(init)
main.add_command(run)

main.add_command(build)
main.add_command(deploy)
main.add_command(exit)

main.add_command(adapter)
main.add_command(plugin)

if __name__ == "__main__":
    main()
