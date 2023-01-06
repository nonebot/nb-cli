from pathlib import Path

from .model import Driver as Driver
from .model import Plugin as Plugin
from .model import Adapter as Adapter
from .model import SimpleInfo as SimpleInfo
from .model import NoneBotConfig as NoneBotConfig
from .parser import ConfigManager as ConfigManager

GLOBAL_CONFIG = ConfigManager()
