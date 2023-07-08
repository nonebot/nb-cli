import json

from jinja2.ext import Extension


class UnJsonifyExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.filters["unjsonify"] = json.loads
