import os
import sys
import sysconfig

# consts
ENTRYPOINT_GROUP = "nb"
# SHELL = os.getenv("SHELL", "")
# WINDOWS = sys.platform.startswith("win") or (
#     sys.platform == "cli" and os.name == "nt"
# )
# MINGW = sysconfig.get_platform().startswith("mingw")
# MACOS = sys.platform == "darwin"

# context keys
MANAGER_KEY = "nb.config_manager"
CONFIG_KEY = "nb.config"

GET_BUILTIN_PLUGINS_SCRIPT = """
import nonebot
print(nonebot.__path__[0])
""".strip()
