from nb_cli.compat import model_dump

from .store import Driver, load_module_data, load_unpublished_modules


async def list_drivers(
    query: str | None = None, include_unpublished: bool = False
) -> list[Driver]:
    drivers = await load_module_data("driver")
    if include_unpublished:
        drivers = drivers + await load_unpublished_modules(Driver)
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
