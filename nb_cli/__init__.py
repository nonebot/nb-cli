from cashews import Cache
from importlib_metadata import EntryPoint, version, entry_points

from .i18n import _ as _

try:
    __version__ = version("nb-cli")
except Exception:
    __version__ = None

cache = Cache("nb")
cache.setup("mem://")

from .cli import run_sync
from .cli import cli as cli_sync
from .consts import PLUGINS_GROUP
from .handlers import install_signal_handler


def load_plugins():
    entrypoint: EntryPoint
    for entrypoint in entry_points(group=PLUGINS_GROUP):
        entrypoint.load()()


async def cli_main(*args, **kwargs):
    install_signal_handler()
    load_plugins()
    return await run_sync(cli_sync)(*args, **kwargs)
