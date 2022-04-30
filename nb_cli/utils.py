from pathlib import Path
from typing import List, Optional, TypedDict

import click
from prompt_toolkit.styles import Style
from pydantic import BaseModel

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


class Adapter(BaseModel):
    module_name: str
    project_link: str
    name: str
    desc: str


class Plugin(BaseModel):
    module_name: str
    project_link: str
    name: str
    desc: str


class Driver(BaseModel):
    module_name: str
    project_link: str
    name: str
    desc: str


class CacheDict(TypedDict):
    adapter: Optional[List[str]]
    driver: Optional[List[str]]
    plugin: Optional[List[str]]


class ModuleCache:
    def __init__(self) -> None:
        self.nb_cli_directory = Path.home() / ".nb_cli"
        self.nb_cli_directory.mkdir(parents=True, exist_ok=True)
        self.cache: CacheDict = self._load_cache()

    def _load_cache(self) -> CacheDict:
        cache: CacheDict = {
            "adapter": None,
            "driver": None,
            "plugin": None,
        }
        for module_name in cache.keys():
            file_path = self.nb_cli_directory / f"{module_name}s.txt"
            if file_path.is_file():
                cache[module_name] = list(map(lambda x: x.strip(), file_path.read_text().split("\n")))  # type: ignore

        return cache

    def get_cache(self, module_name: str) -> Optional[List[str]]:
        module_name = module_name.lower()
        if module_name not in self.cache:
            return None
        return self.cache[module_name]  # type: ignore

    def flush_cache(self, module_name: str, module_cache: List[str]) -> None:
        module_name = module_name.lower()
        if module_cache is None or module_name not in self.cache:
            return None

        self.cache[module_name] = module_cache  # type: ignore
        file_path = self.nb_cli_directory / f"{module_name}s.txt"
        file_path.write_text(data="\n".join(module_cache))


Cache: ModuleCache = ModuleCache()
