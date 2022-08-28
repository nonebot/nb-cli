import os
import subprocess
from contextlib import suppress
from typing import Any, List, Union

import click

from nb_cli.consts import (
    WINDOWS,
    BOT_STARTUP_TEMPLATE,
    ADAPTER_IMPORT_TEMPLATE,
    ADAPTER_REGISTER_TEMPLATE,
    LOAD_BUILTIN_PLUGIN_TEMPLATE,
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


def run_script(cmd: list[str], **kwargs: Any) -> Union[int, str, bytes, None]:
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
