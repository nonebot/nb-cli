from pathlib import Path
from typing import Optional

from cookiecutter.main import cookiecutter

from nb_cli.config import Adapter
from nb_cli.compat import model_dump

from .store import load_module_data

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "adapter"


def create_adapter(
    adapter_name: str,
    output_dir: str = ".",
    template: Optional[str] = None,
):
    cookiecutter(
        str(TEMPLATE_ROOT.resolve()) if template is None else template,
        no_input=True,
        output_dir=output_dir,
        extra_context={"adapter_name": adapter_name},
    )


async def list_adapters(query: Optional[str] = None) -> list[Adapter]:
    adapters = await load_module_data("adapter")
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
