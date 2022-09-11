import os
import subprocess
from pathlib import Path
from contextlib import suppress
from typing import Any, List, Union, Optional, overload

import click
from prompt_toolkit.styles import Style

from .consts import (
    MACOS,
    WINDOWS,
    BOT_STARTUP_TEMPLATE,
    ADAPTER_IMPORT_TEMPLATE,
    ADAPTER_REGISTER_TEMPLATE,
    LOAD_BUILTIN_PLUGIN_TEMPLATE,
)

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


def gen_script(adapters: List[str], builtin_plugins: List[str]) -> str:
    adapters_import: List[str] = []
    adapters_register: List[str] = []
    for adapter in adapters:
        adapters_import.append(
            ADAPTER_IMPORT_TEMPLATE.format(
                path=adapter, name=adapter.replace(".", "").upper()
            )
        )
        adapters_register.append(
            ADAPTER_REGISTER_TEMPLATE.format(
                name=adapter.replace(".", "").upper()
            )
        )

    builtin_plugins_load: List[str] = [
        LOAD_BUILTIN_PLUGIN_TEMPLATE.format(name=plugin)
        for plugin in builtin_plugins
    ]

    return BOT_STARTUP_TEMPLATE.format(
        adapters_import="\n".join(adapters_import),
        adapters_register="\n".join(adapters_register),
        builtin_plugins_load="\n".join(builtin_plugins_load),
    )


def list_to_shell_command(cmd: list[str]) -> str:
    return " ".join(
        f'"{token}"' if " " in token and token[0] not in {"'", '"'} else token
        for token in cmd
    )


def decode(
    string: Union[bytes, str], encodings: Union[List[str], None] = None
) -> str:
    if not isinstance(string, bytes):
        return string

    encodings = encodings or ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        with suppress(UnicodeEncodeError, UnicodeDecodeError):
            return string.decode(encoding)

    return string.decode(encodings[0], errors="ignore")


def encode(string: str, encodings: Union[List[str], None] = None) -> bytes:
    if isinstance(string, bytes):
        return string

    encodings = encodings or ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        with suppress(UnicodeEncodeError, UnicodeDecodeError):
            return string.encode(encoding)

    return string.encode(encodings[0], errors="ignore")


@overload
def run_script(cmd: List[str], *, call: bool, **kwargs: Any) -> int:
    ...


@overload
def run_script(
    cmd: List[str], *, input_: Optional[str], **kwargs: Any
) -> bytes:
    ...


def run_script(cmd: List[str], **kwargs: Any) -> Union[int, str, bytes, None]:
    """
    Run a command inside the Python environment.
    """
    call = kwargs.pop("call", False)
    input_ = kwargs.pop("input_", None)
    env = kwargs.pop("env", dict(os.environ))
    capture_output = kwargs.pop("capture_output", False)
    try:
        if WINDOWS:
            kwargs["shell"] = True
        command: Union[str, list[str]]
        if kwargs.get("shell", False):
            command = list_to_shell_command(cmd)
        else:
            command = cmd
        if input_:
            output = subprocess.run(
                command,
                input=encode(input_),
                capture_output=capture_output,
                check=True,
                **kwargs,
            ).stdout
        elif call:
            return subprocess.call(
                command, stderr=subprocess.STDOUT, env=env, **kwargs
            )
        else:
            output = subprocess.check_output(
                command, stderr=subprocess.STDOUT, env=env, **kwargs
            )
        return decode(output)
    except Exception as e:
        click.secho(repr(e), fg="red")


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
