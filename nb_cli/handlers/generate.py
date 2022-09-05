from pathlib import Path

from nb_cli.utils import gen_script
from nb_cli.config import LocalConfig, ConfigManager


def generate_script(
    config: str = "pyproject.toml",
    file: str = "bot.py",
):
    local_config: LocalConfig = ConfigManager.get_local_config(config)

    with open(Path(file).resolve(), "w") as f:
        script = gen_script(
            local_config.get_adapters(),
            local_config.get_builtin_plugins(),
        )
        f.write(script)
