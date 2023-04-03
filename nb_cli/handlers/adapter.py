from pathlib import Path
from typing import List, Optional

from cookiecutter.main import cookiecutter

from nb_cli.config import Adapter

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


async def list_adapters(query: Optional[str] = None) -> List[Adapter]:
    adapters = await load_module_data("adapter")
    if query is None:
        return adapters

    return [
        adapter
        for adapter in adapters
        if any(query in value for value in adapter.dict().values())
    ]
