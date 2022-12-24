from typing import List, Optional

from pydantic import BaseModel


# CLI Configs
class Filter(BaseModel):
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None


class CLIConfig(BaseModel):
    python: str = "python"
    plugins: Filter = Filter()
    scripts: Filter = Filter()


# NoneBot Configs
class SimpleInfo(BaseModel):
    name: str
    module_name: str


class Adapter(SimpleInfo):
    project_link: str
    desc: str


class Plugin(SimpleInfo):
    project_link: str
    desc: str


class Driver(SimpleInfo):
    project_link: str
    desc: str


class NoneBotConfig(BaseModel):
    adapters: List[SimpleInfo] = []
    plugins: List[str] = []
    plugin_dirs: List[str] = []
    builtin_plugins: List[str] = []


class Config(BaseModel):
    nb_cli: CLIConfig = CLIConfig()
    nonebot: NoneBotConfig = NoneBotConfig()
