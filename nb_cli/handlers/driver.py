from typing import Optional

from nb_cli.compat import model_dump

from .store import Driver, load_module_data


async def list_drivers(query: Optional[str] = None) -> list[Driver]:
    drivers = await load_module_data("driver")
    if query is None:
        return drivers

    return [
        driver
        for driver in drivers
        if any(
            query in value
            for value in model_dump(
                driver, include={"name", "module_name", "project_link", "desc"}
            ).values()
        )
    ]
