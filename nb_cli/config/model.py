from typing import List, Optional

from pydantic import Extra, BaseModel


# CLI Configs
class Filter(BaseModel):
    includes: Optional[List[str]] = None
    excludes: Optional[List[str]] = None


class Config(BaseModel, extra=Extra.allow):
    python: str = "python"
    scripts: Filter = Filter()


# NoneBot Configs
class SimpleInfo(BaseModel):
    name: str
    module_name: str


class Adapter(SimpleInfo):
    project_link: str
    desc: str

    class Config:
        module_name = "adapters"


class Plugin(SimpleInfo):
    project_link: str
    desc: str

    class Config:
        module_name = "plugins"


class Driver(SimpleInfo):
    project_link: str
    desc: str

    class Config:
        module_name = "drivers"


class NoneBotConfig(BaseModel, extra=Extra.allow):
    adapters: List[SimpleInfo] = []
    plugins: List[str] = []
    plugin_dirs: List[str] = []
    builtin_plugins: List[str] = []
