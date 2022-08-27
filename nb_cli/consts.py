import os
import sys
import sysconfig

BOT_STARTUP_TEMPLATE = """\
import nonebot
{adapters_import}

nonebot.init()
app = nonebot.get_asgi()

driver = nonebot.get_driver()
{adapters_register}
{builtin_plugins_load}

nonebot.load_from_toml("pyproject.toml")


if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
"""
ADAPTER_IMPORT_TEMPLATE = """\
from {path} import Adapter as {name}Adapter
"""
ADAPTER_REGISTER_TEMPLATE = """\
driver.register_adapter({name}Adapter)
"""
LOAD_BUILTIN_PLUGIN_TEMPLATE = """\
nonebot.load_builtin_plugins("{name}")
"""

SHELL = os.getenv("SHELL", "")
WINDOWS = sys.platform.startswith("win") or (
    sys.platform == "cli" and os.name == "nt"
)
MINGW = sysconfig.get_platform().startswith("mingw")
MACOS = sys.platform == "darwin"