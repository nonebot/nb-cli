from importlib.metadata import version

from cashews import Cache

try:
    __version__ = version("nb-cli")
except Exception:
    __version__ = None

cache = Cache("nb")
cache.setup("mem://")

from .cli import run_sync
from .cli import cli as cli_sync
from .handlers import install_signal_handler


async def cli_main(*args, **kwargs):
    install_signal_handler()
    return await run_sync(cli_sync)(*args, **kwargs)
