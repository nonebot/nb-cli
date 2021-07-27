#type: ignore

import os
import shutil


def remove(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)
    elif os.path.isdir(filepath):
        shutil.rmtree(filepath)


if {{cookiecutter.sub_plugin}}:
    remove(os.path.join("plugins", ".gitkeep"))
else:
    remove(os.path.join("plugins"))
