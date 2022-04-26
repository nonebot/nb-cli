from typing import List, Optional

import click
from prompt_toolkit.styles import Style

default_style = Style.from_dict(
    {
        "questionmark": "fg:#673AB7 bold",
        "question": "",
        "sign": "",
        "unsign": "",
        "selected": "",
        "pointer": "bold",
        "annotation": "",
        "answer": "bold",
    }
)


class ClickAliasedCommand(click.Command):
    def __init__(self, *args, **kwargs) -> None:
        aliases = kwargs.pop("aliases", None)
        self._aliases: Optional[List[str]] = aliases
        super().__init__(*args, **kwargs)


class ClickAliasedGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super(ClickAliasedGroup, self).__init__(*args, **kwargs)
        self._commands = {}
        self._aliases = {}

    def command(self, *args, **kwargs):
        cls = kwargs.pop("cls", ClickAliasedCommand)
        return super(ClickAliasedGroup, self).command(*args, cls=cls, **kwargs)

    def group(self, *args, **kwargs):
        aliases = kwargs.pop("aliases", [])
        decorator = super(ClickAliasedGroup, self).group(*args, **kwargs)
        if not aliases:
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            if aliases:
                self._commands[cmd.name] = aliases
                for alias in aliases:
                    self._aliases[alias] = cmd.name
            return cmd

        return _decorator

    def resolve_alias(self, cmd_name):
        if cmd_name in self._aliases:
            return self._aliases[cmd_name]
        return cmd_name

    def add_command(
        self, cmd: click.Command, name: Optional[str] = None
    ) -> None:
        aliases: Optional[List[str]] = getattr(cmd, "_aliases", None)
        if aliases and isinstance(cmd, ClickAliasedCommand):
            self._commands[cmd.name] = aliases
            for alias in aliases:
                self._aliases[alias] = cmd.name
        return super(ClickAliasedGroup, self).add_command(cmd, name=name)

    def get_command(self, ctx, cmd_name):
        cmd_name = self.resolve_alias(cmd_name)
        command = super(ClickAliasedGroup, self).get_command(ctx, cmd_name)
        if command:
            return command

    def format_commands(self, ctx, formatter):
        rows = []

        sub_commands = self.list_commands(ctx)

        max_len = max(len(cmd) for cmd in sub_commands)
        limit = formatter.width - 6 - max_len

        for sub_command in sub_commands:
            cmd = self.get_command(ctx, sub_command)
            if cmd is None:
                continue
            if hasattr(cmd, "hidden") and cmd.hidden:
                continue
            if sub_command in self._commands:
                aliases = ",".join(sorted(self._commands[sub_command]))
                sub_command = f"{sub_command} ({aliases})"
            cmd_help = cmd.get_short_help_str(limit)
            rows.append((sub_command, cmd_help))

        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)
