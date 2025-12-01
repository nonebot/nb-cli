from pathlib import Path

from cookiecutter.main import cookiecutter

from nb_cli.compat import model_dump
from nb_cli.exceptions import ProjectInvalidError
from nb_cli.config import Adapter, NoneBotConfig, LegacyNoneBotConfig

from .meta import get_nonebot_config, requires_project_root
from .store import load_module_data, load_unpublished_modules

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "adapter"


def create_adapter(
    adapter_name: str,
    output_dir: str = ".",
    template: str | None = None,
):
    cookiecutter(
        str(TEMPLATE_ROOT.resolve()) if template is None else template,
        no_input=True,
        output_dir=output_dir,
        extra_context={"adapter_name": adapter_name},
    )


async def list_adapters(
    query: str | None = None, include_unpublished: bool = False
) -> list[Adapter]:
    adapters = await load_module_data("adapter")
    if include_unpublished:
        adapters = adapters + await load_unpublished_modules(Adapter)
    if query is None:
        return adapters

    return [
        adapter
        for adapter in adapters
        if any(
            query in value
            for value in model_dump(
                adapter, include={"name", "module_name", "project_link", "desc"}
            ).values()
        )
    ]


@requires_project_root
async def list_installed_adapters(*, cwd: Path | None = None) -> list[Adapter]:
    config_data = get_nonebot_config(cwd)
    adapters = await load_module_data("adapter") + await load_unpublished_modules(
        Adapter
    )

    result: list[Adapter] = []

    if isinstance(config_data, NoneBotConfig):
        adapter_info = config_data.adapters
        allowed_pairs = {
            (pkg_name, m.module_name)
            for pkg_name, modules in adapter_info.items()
            for m in modules
        }
        for adapter in adapters:
            if (adapter.project_link, adapter.module_name) in allowed_pairs:
                result.append(adapter)
    elif isinstance(config_data, LegacyNoneBotConfig):
        adapter_info = config_data.adapters
        allowed_pairs = {m.module_name for m in adapter_info}
        for adapter in adapters:
            if adapter.module_name in allowed_pairs:
                result.append(adapter)
    else:
        raise ProjectInvalidError("Invalid config data type")

    return result
