from importlib.metadata import version

try:
    __version__ = version("nb-cli")
except Exception:
    __version__ = None

from .commands import cli as cli
