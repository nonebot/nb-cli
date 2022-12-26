from typing import List, Optional

from nb_cli.config import Adapter

from .meta import load_module_data


async def list_adapters(query: Optional[str] = None) -> List[Adapter]:
    adapters = await load_module_data("adapter")
    if query is None:
        return adapters

    return [
        adapter
        for adapter in adapters
        if any(query in value for value in adapter.dict().values())
    ]
