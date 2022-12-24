from typing import Dict, List, Optional
from functools import partial, lru_cache

import click
from prompt_toolkit.styles import Style

from nb_cli.config import Config
from nb_cli.consts import CONFIG_KEY
from nb_cli.handlers import run_script, list_scripts

CLI_DEFAULT_STYLE = Style.from_dict(
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
        self._commands: Dict[str, List[str]] = {}
        self._aliases: Dict[str, str] = {}

    def command(self, *args, **kwargs):
        cls = kwargs.pop("cls", ClickAliasedCommand)
        return super(ClickAliasedGroup, self).command(*args, cls=cls, **kwargs)

    def group(self, *args, **kwargs):
        aliases: Optional[List[str]] = kwargs.pop("aliases", None)
        decorator = super(ClickAliasedGroup, self).group(*args, **kwargs)
        if not aliases:
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            if cmd.name:
                self.add_aliases(cmd.name, aliases)
            return cmd

        return _decorator

    def add_aliases(self, cmd_name: str, aliases: List[str]) -> None:
        self._commands[cmd_name] = aliases
        for alias in aliases:
            self._aliases[alias] = cmd_name

    def resolve_alias(self, cmd_name):
        return (
            self._aliases[cmd_name] if cmd_name in self._aliases else cmd_name
        )

    def add_command(
        self, cmd: click.Command, name: Optional[str] = None
    ) -> None:
        aliases: Optional[List[str]] = getattr(cmd, "_aliases", None)
        if aliases and isinstance(cmd, ClickAliasedCommand) and cmd.name:
            self.add_aliases(cmd.name, aliases)
        return super(ClickAliasedGroup, self).add_command(cmd, name=name)

    def get_command(self, ctx: click.Context, cmd_name: str):
        cmd_name = self.resolve_alias(cmd_name)
        if command := super(ClickAliasedGroup, self).get_command(ctx, cmd_name):
            return command

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ):
        rows = []

        sub_commands = self.list_commands(ctx)

        max_len = max(len(cmd) for cmd in sub_commands)
        limit = formatter.width - 6 - max_len

        for sub_command in sub_commands:
            cmd = self.get_command(ctx, sub_command)
            if cmd is None:
                continue
            if cmd.hidden:
                continue
            if sub_command in self._commands:
                aliases = ",".join(sorted(self._commands[sub_command]))
                sub_command = f"{sub_command} ({aliases})"
            cmd_help = cmd.get_short_help_str(limit)
            rows.append((sub_command, cmd_help))

        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


class CLIMainGroup(ClickAliasedGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @lru_cache
    def _load_scripts(self, ctx: click.Context) -> List[click.Command]:
        config: Config = ctx.meta[CONFIG_KEY]
        scripts = list_scripts(python_path=config.nb_cli.python)
        return [
            self.command(name=script, help=f"Run script {script!r}")(
                partial(
                    run_script,
                    script_name=script,
                    adapters=config.nonebot.adapters,
                    builtin_plugins=config.nonebot.builtin_plugins,
                    python_path=config.nb_cli.python,
                )
            )
            for script in scripts
        ]

    def get_command(
        self, ctx: click.Context, cmd_name: str
    ) -> Optional[click.Command]:
        if command := super().get_command(ctx, cmd_name):
            return command
        scripts = self._load_scripts(ctx)
        return next(filter(lambda x: x.name == cmd_name, scripts), None)

    def list_commands(self, ctx: click.Context) -> List[str]:
        return super().list_commands(ctx) + [
            cmd.name for cmd in self._load_scripts(ctx) if cmd.name
        ]
