from typing import Optional

from .store import Driver, load_module_data


async def list_drivers(query: Optional[str] = None) -> list[Driver]:
    drivers = await load_module_data("driver")
    if query is None:
        return drivers

    return [
        driver
        for driver in drivers
        if any(query in value for value in driver.dict().values())
    ]
