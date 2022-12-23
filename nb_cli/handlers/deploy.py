import os
from typing import List, Callable, Iterable

from noneprompt import Choice, ListPrompt

from nb_cli.utils import default_style
from nb_cli.loader import NoneBotProcess
from nb_cli.loader.reloader import WatchFilesReload


def run_bot(script: str = "bot.py", file: str = "pyproject.toml") -> bool:
    config = ConfigManager.get_local_config(file)

    if os.path.isfile(script):
        process = NoneBotProcess(config, script)
    else:
        process = NoneBotProcess(config)

    if config.get("reload"):
        WatchFilesReload(config, process).run()
    else:
        process.run()

    return True
