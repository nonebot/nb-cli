import shutil
import textwrap
from typing import List, Union, Optional

import click
from pydantic import BaseModel
from PyInquirer import style_from_dict, Token

list_style = style_from_dict({
    Token.Separator: "#6C6C6C",
    Token.QuestionMark: "#673AB7 bold",
    Token.Selected: "#5F819D",
    Token.Pointer: "#FF9D00 bold",
    Token.Instruction: "",
    Token.Answer: "#5F819D bold",
    Token.Question: "",
})


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

    def add_command(self,
                    cmd: click.Command,
                    name: Optional[str] = None) -> None:
        aliases: Optional[List[str]] = getattr(cmd, "_aliases", None)
        if aliases:
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


class Adapter(BaseModel):
    id: str
    link: str
    name: str
    desc: str
    author: str
    repo: str


class Plugin(BaseModel):
    id: str
    link: str
    name: str
    desc: str
    author: str
    repo: str


def print_package_results(hits: Union[List[Plugin], List[Adapter]],
                          name_column_width: Optional[int] = None,
                          terminal_width: Optional[int] = None):
    if not hits:
        return

    if name_column_width is None:
        name_column_width = max(
            [len(f"{hit.name} ({hit.link})") for hit in hits]) + 4
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size()[0]

    for hit in hits:
        name = f"{hit.name} ({hit.link})"
        summary = hit.desc
        target_width = terminal_width - name_column_width - 5
        if target_width > 10:
            # wrap and indent summary to fit terminal
            summary_lines = textwrap.wrap(summary, target_width)
            summary = ("\n" + " " * (name_column_width + 3)).join(summary_lines)

        line = f"{name:{name_column_width}} - {summary}"
        try:
            print(line)
        except UnicodeEncodeError:
            pass
