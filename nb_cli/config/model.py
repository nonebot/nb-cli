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


class Adapter(SimpleInfo):
    __module_name__ = "adapters"

    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: Optional[bool] = None
    time: datetime
    version: str

    @field_serializer("time")
    def time_serializer(self, dt: datetime):
        return dt.isoformat()


class Plugin(SimpleInfo):
    __module_name__ = "plugins"

    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: Optional[bool] = None
    valid: Optional[bool] = None
    time: datetime
    version: str

    @field_serializer("time")
    def time_serializer(self, dt: datetime):
        return dt.isoformat()


class Driver(SimpleInfo):
    __module_name__ = "drivers"

    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: Optional[bool] = None
    time: datetime
    version: str

    @field_serializer("time")
    def time_serializer(self, dt: datetime):
        return dt.isoformat()


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
