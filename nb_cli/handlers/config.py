from typing import List, Union

from nb_cli.handlers.utils import get_normalizer
from nb_cli.config import LocalConfig, ConfigManager


def update_config(config: LocalConfig, key: str, value: Union[str, list, None]):
    if value is None:
        config.unset(key)
    else:
        if isinstance(value, str):
            value = get_normalizer(key)(value)
        config.update(key, value)


def config_no_subcommand(
    file: str, list: bool, unset: bool, key: str, value: str, element: List[str]
):
    config = ConfigManager.get_local_config(file)

    if list:
        config.print()
    elif unset:
        update_config(config, key, None)
    elif key is not None and value is not None:
        if len(element) > 0:
            update_config(config, key, element)
        else:
            update_config(config, key, value)
