from pydantic import BaseModel
from nb_cli.compat import PYDANTIC_V2, ConfigDict

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
