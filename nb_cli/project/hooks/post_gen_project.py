#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil


def remove(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)
    elif os.path.isdir(filepath):
        shutil.rmtree(filepath)


remove(os.path.join("{{cookiecutter.source_dir}}", "plugins", ".gitkeep"))
