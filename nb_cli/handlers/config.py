from typing import Optional

from nb_cli.config import LocalConfig
from nb_cli.handlers.utils import get_normalizer


def update_config(config: LocalConfig, key: str, value: Optional[str]):
    if value is None:
        config.unset(key)
    else:
        value = get_normalizer(key)(value)
        config.update(key, value)
