import os
import sys
import sysconfig

# consts
ENTRYPOINT_GROUP = "nb"
SHELL = os.getenv("SHELL", "")
WINDOWS = sys.platform.startswith("win") or (
    sys.platform == "cli" and os.name == "nt"
)
MINGW = sysconfig.get_platform().startswith("mingw")
MACOS = sys.platform == "darwin"

# context keys
MANAGER_KEY = "nb.config_manager"
CONFIG_KEY = "nb.config"

# nb run
BOT_LOAD_TEMPLATE = """
import nonebot
{adapters_import}

nonebot.init()
app = nonebot.get_asgi()

driver = nonebot.get_driver()
{adapters_register}
{builtin_plugins_load}

nonebot.load_from_toml("pyproject.toml")
""".strip()

BOT_RUN_TEMPLATE = """
{preload_bot}

if __name__ == "__main__":
    nonebot.run()
""".strip()

ADAPTER_IMPORT_TEMPLATE = """
from {path} import Adapter as {name}Adapter
""".strip()

ADAPTER_REGISTER_TEMPLATE = """
driver.register_adapter({name}Adapter)
""".strip()

LOAD_BUILTIN_PLUGIN_TEMPLATE = """
nonebot.load_builtin_plugins({plugins})
""".strip()

GET_BUILTIN_PLUGINS_SCRIPT = """
import nonebot
print(nonebot.__path__[0])
""".strip()

# nb scripts
GET_SCRIPTS_SCRIPT = f"""
import json
from importlib.metadata import entry_points
print(json.dumps(entry_points(group="{ENTRYPOINT_GROUP}").names))
""".strip()
RUN_SCRIPTS_SCRIPT = f"""
from importlib.metadata import entry_points

{{preload_bot}}

if __name__ == "__main__":
    entry_points(group="{ENTRYPOINT_GROUP}", name="{{script_name}}")[0].load()()
""".strip()
