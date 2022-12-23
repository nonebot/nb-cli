from typing import List, Optional

from pydantic import BaseModel


class Filter(BaseModel):
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None


class CLIConfig(BaseModel):
    python: str = "python"
    plugins: Filter = Filter()
    scripts: Filter = Filter()


class NoneBotConfig(BaseModel):
    adapters: List[str] = []
    plugins: List[str] = []
    plugin_dirs: List[str] = []
    builtin_plugins: List[str] = []


class Config(BaseModel):
    nb_cli: CLIConfig = CLIConfig()
    nonebot: NoneBotConfig = NoneBotConfig()
