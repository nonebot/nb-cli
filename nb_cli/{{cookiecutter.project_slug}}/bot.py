#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot

# Custom your logger
# 
# from nonebot.log import logger, default_format
# logger.add("error.log",
#            rotation="00:00",
#            diagnose=False,
#            level="ERROR",
#            format=default_format)

# You can pass some keyword args config to init function
nonebot.init()
app = nonebot.get_asgi()
{% if cookiecutter.load_builtin == "True" %}
nonebot.load_builtin_plugins(){% endif %}
nonebot.load_plugins("{{ cookiecutter.source_dir }}/plugins")

# Modify some config / config depends on loaded configs
# 
# config = nonebot.get_driver().config
# do something...


if __name__ == "__main__":
    nonebot.run(app="bot:app")
