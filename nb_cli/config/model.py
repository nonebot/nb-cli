from typing import Optional

from pydantic import BaseModel

from nb_cli.compat import PYDANTIC_V2, ConfigDict


class SimpleInfo(BaseModel):
    name: str
    module_name: str


class Adapter(SimpleInfo):
    __module_name__ = "adapters"

    project_link: str
    desc: str
    is_official: Optional[bool] = None


class Plugin(SimpleInfo):
    __module_name__ = "plugins"

    project_link: str
    desc: str
    is_official: Optional[bool] = None
    valid: Optional[bool] = None


class Driver(SimpleInfo):
    __module_name__ = "drivers"

    project_link: str
    desc: str
    is_official: Optional[bool] = None


class NoneBotConfig(BaseModel):
    if PYDANTIC_V2:  # pragma: pydantic-v2
        model_config = ConfigDict(extra="allow")
    else:  # pragma: pydantic-v1

        class Config(ConfigDict):
            extra = "allow"  # type: ignore

    adapters: list[SimpleInfo] = []
    plugins: list[str] = []
    plugin_dirs: list[str] = []
    builtin_plugins: list[str] = []
