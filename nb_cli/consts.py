import os
import sys

# consts
PLUGINS_GROUP = "nb"
SCRIPTS_GROUP = "nb_scripts"
REQUIRES_PYTHON = (3, 10)
DEFAULT_DRIVER = ("FastAPI",)
# SHELL = os.getenv("SHELL", "")
WINDOWS = sys.platform.startswith("win") or (sys.platform == "cli" and os.name == "nt")
# MINGW = sysconfig.get_platform().startswith("mingw")
# MACOS = sys.platform == "darwin"
