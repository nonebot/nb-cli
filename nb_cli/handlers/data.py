import os
import sys

import nonestorage

WINDOWS = sys.platform.startswith("win") or (sys.platform == "cli" and os.name == "nt")

CACHE_DIR = nonestorage.user_cache_dir("nb-cli")
DATA_DIR = nonestorage.user_data_dir("nb-cli")
CONFIG_DIR = nonestorage.user_config_dir("nb-cli")
