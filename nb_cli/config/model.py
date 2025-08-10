import operator
import functools
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, field_serializer

from nb_cli.compat import PYDANTIC_V2, ConfigDict


class Tag(BaseModel):
    """标签"""

    label: str
    color: str


class SimpleInfo(BaseModel):
    name: str
    module_name: str


class PackageInfo(SimpleInfo):
    project_link: str
    time: datetime
    version: str

    @field_serializer("time")
    def time_serializer(self, dt: datetime):
        return dt.isoformat()


class Adapter(PackageInfo):
    __module_name__ = "adapters"

    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: Optional[bool] = None


class Plugin(PackageInfo):
    __module_name__ = "plugins"

    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: Optional[bool] = None
    valid: Optional[bool] = None
    skip_test: bool = False


class Driver(PackageInfo):
    __module_name__ = "drivers"

    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: Optional[bool] = None


class NoneBotConfig(BaseModel):
    if PYDANTIC_V2:  # pragma: pydantic-v2
        model_config = ConfigDict(extra="allow")
    else:  # pragma: pydantic-v1

        class Config(ConfigDict):
            extra = "allow"  # type: ignore

    adapters: dict[str, list[SimpleInfo]] = {}
    plugins: dict[str, list[str]] = {}
    plugin_dirs: list[str] = []
    builtin_plugins: list[str] = []

    def get_adapters(self) -> list[SimpleInfo]:
        return functools.reduce(operator.iadd, self.adapters.values(), [])

    def get_plugins(self) -> list[str]:
        return functools.reduce(operator.iadd, self.plugins.values(), [])


class LegacyNoneBotConfig(BaseModel):
    if PYDANTIC_V2:  # pragma: pydantic-v2
        model_config = ConfigDict(extra="allow")
    else:  # pragma: pydantic-v1

        class Config(ConfigDict):
            extra = "allow"  # type: ignore

    adapters: list[SimpleInfo] = []
    plugins: list[str] = []
    plugin_dirs: list[str] = []
    builtin_plugins: list[str] = []

    def get_adapters(self) -> list[SimpleInfo]:
        return self.adapters

    def get_plugins(self) -> list[str]:
        return self.plugins
