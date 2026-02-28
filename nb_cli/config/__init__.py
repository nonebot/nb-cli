from logging import Logger

from nb_cli.log import ClickHandler

from .model import Adapter as Adapter
from .model import Driver as Driver
from .model import LegacyNoneBotConfig as LegacyNoneBotConfig
from .model import NoneBotConfig as NoneBotConfig
from .model import PackageInfo as PackageInfo
from .model import Plugin as Plugin
from .model import SimpleInfo as SimpleInfo
from .parser import ConfigManager as ConfigManager

_logger = Logger(__name__)
_logger.addHandler(ClickHandler())
GLOBAL_CONFIG = ConfigManager(logger=_logger)
