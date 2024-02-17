from pydantic import Extra, BaseModel


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
    adapters: list[SimpleInfo] = []
    plugins: list[str] = []
    plugin_dirs: list[str] = []
    builtin_plugins: list[str] = []
