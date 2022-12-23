import os
from pathlib import Path
from functools import partial, lru_cache
from typing import Any, Dict, List, Union, Optional, overload

import click
from prompt_toolkit.styles import Style

from nb_cli.config import Config
from nb_cli.handlers import run_script, list_scripts

from .consts import MACOS, WINDOWS, CONFIG_KEY

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


def list_to_shell_command(cmd: list[str]) -> str:
    return " ".join(
        f'"{token}"' if " " in token and token[0] not in {"'", '"'} else token
        for token in cmd
    )


def _get_win_folder_from_registry(csidl_name):
    import winreg as _winreg

    shell_folder_name = {
        "CSIDL_APPDATA": "AppData",
        "CSIDL_COMMON_APPDATA": "Common AppData",
        "CSIDL_LOCAL_APPDATA": "Local AppData",
    }[csidl_name]

    key = _winreg.OpenKey(
        _winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
    )
    dir, type = _winreg.QueryValueEx(key, shell_folder_name)

    return dir


def _get_win_folder_with_ctypes(csidl_name):
    import ctypes

    csidl_const = {
        "CSIDL_APPDATA": 26,
        "CSIDL_COMMON_APPDATA": 35,
        "CSIDL_LOCAL_APPDATA": 28,
    }[csidl_name]

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl_const, None, 0, buf)

    # Downgrade to short path name if have highbit chars. See
    # <http://bugs.activestate.com/show_bug.cgi?id=85099>.
    has_high_char = False
    for c in buf:
        if ord(c) > 255:
            has_high_char = True
            break
    if has_high_char:
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    return buf.value


def get_data_dir(version: Optional[str] = None) -> Path:
    home = os.getenv("NONEBOT_CLI_HOME")
    if home:
        return Path(home).expanduser()

    if WINDOWS:
        try:
            from ctypes import windll

            _get_win_folder = _get_win_folder_with_ctypes
        except ImportError:
            _get_win_folder = _get_win_folder_from_registry
        const = "CSIDL_APPDATA"
        path = os.path.normpath(_get_win_folder(const))
        path = os.path.join(path, "nonebot_cli")
    elif MACOS:
        path = os.path.expanduser("~/Library/Application Support/nonebot_cli")
    else:
        path = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        path = os.path.join(path, "nonebot_cli")

    if version:
        path = os.path.join(path, version)

    return Path(path)


DATA_DIR = get_data_dir()


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
            self.command(name=script)(
                partial(run_script, script_name=script, config=config)
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
        return super().list_commands(ctx)
