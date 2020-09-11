#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot


nonebot.init(){% if cookiecutter.load_builtin %}
nonebot.load_builtin_plugins(){% endif %}
nonebot.load_plugins("{{ cookiecutter.source_dir }}/plugins")

app = nonebot.get_asgi()

if __name__ == "__main__":
    nonebot.run(app="bot:app")
