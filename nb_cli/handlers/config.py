from typing import List, Union

from nb_cli.consts import NONEBOT_ARRAY_CONFIGS
from nb_cli.handlers.utils import get_normalizer
from nb_cli.config import LocalConfig, ConfigManager


def update_config(config: LocalConfig, key: str, value: Union[str, list, None]):
    if value is None:
        config.unset(key)
    else:
        value = get_normalizer(key)(value)
        config.update(key, value)


def config_no_subcommand(
    file: str, list: bool, unset: bool, key: str, value: str, element: List[str]
):
    config = ConfigManager.get_local_config(file)

    if list:
        config.print()
    if unset:
        update_config(config, key, None)
    if key is not None:
        if len(element) == 0 and key in NONEBOT_ARRAY_CONFIGS:
            raise ValueError(
                "No element supplied for array config, please use -e to input element"
            )

        if len(element) > 0:
            update_config(config, key, element)
        else:
            update_config(config, key, value)
