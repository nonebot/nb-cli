import shutil
from asyncio import create_task, as_completed
from typing import TYPE_CHECKING, List, Union, Literal, TypeVar, Optional, overload

import httpx
from wcwidth import wcswidth

from nb_cli import _, cache
from nb_cli.exceptions import ModuleLoadFailed
from nb_cli.config import Driver, Plugin, Adapter

T = TypeVar("T", Adapter, Plugin, Driver)


if TYPE_CHECKING:

    @overload
    async def load_module_data(module_type: Literal["adapter"]) -> List[Adapter]: ...

    @overload
    async def load_module_data(module_type: Literal["plugin"]) -> List[Plugin]: ...

    @overload
    async def load_module_data(module_type: Literal["driver"]) -> List[Driver]: ...

    async def load_module_data(
        module_type: Literal["adapter", "plugin", "driver"]
    ) -> Union[List[Adapter], List[Plugin], List[Driver]]: ...

else:

    @cache(ttl=None)
    async def load_module_data(
        module_type: Literal["adapter", "plugin", "driver"]
    ) -> Union[List[Adapter], List[Plugin], List[Driver]]:
        if module_type == "adapter":
            module_class = Adapter
        elif module_type == "plugin":
            module_class = Plugin
        elif module_type == "driver":
            module_class = Driver
        else:
            raise ValueError(
                _("Invalid module type: {module_type}").format(module_type=module_type)
            )
        module_name: str = getattr(module_class.__config__, "module_name")

        exceptions: List[Exception] = []
        urls = [
            f"https://registry.nonebot.dev/{module_name}.json",
            f"https://cdn.jsdelivr.net/gh/nonebot/registry@results/{module_name}.json",
            f"https://cdn.staticaly.com/gh/nonebot/registry@results/{module_name}.json",
            f"https://jsd.cdn.zzko.cn/gh/nonebot/registry@results/{module_name}.json",
            f"https://mirror.ghproxy.com/https://raw.githubusercontent.com/nonebot/registry/results/{module_name}.json",
            f"https://gh-proxy.com/https://raw.githubusercontent.com/nonebot/registry/results/{module_name}.json",
        ]

        async def _request(url: str) -> httpx.Response:
            async with httpx.AsyncClient() as client:
                return await client.get(url)

        tasks = [create_task(_request(url)) for url in urls]
        for future in as_completed(tasks):
            try:
                resp = await future
                items = resp.json()
                result = [module_class.parse_obj(item) for item in items]
                for task in tasks:
                    if not task.done():
                        task.cancel()
                return result  # type: ignore
            except Exception as e:
                exceptions.append(e)

        raise ModuleLoadFailed(
            _("Failed to get {module_type} list.").format(module_type=module_type),
            exceptions,
        )


def format_package_results(
    hits: List[T],
    name_column_width: Optional[int] = None,
    terminal_width: Optional[int] = None,
) -> str:
    if not hits:
        return ""

    if name_column_width is None:
        name_column_width = (
            max(wcswidth(f"{hit.name} ({hit.project_link})") for hit in hits) + 4
        )
    if terminal_width is None:
        terminal_width = shutil.get_terminal_size()[0]

    lines: List[str] = []
    for hit in hits:
        name = f"{hit.name} ({hit.project_link})"
        summary = hit.desc
        target_width = terminal_width - name_column_width - 5
        if target_width > 10:
            # wrap and indent summary to fit terminal
            summary_lines = []
            while wcswidth(summary) > target_width:
                tmp_length = target_width
                while wcswidth(summary[:tmp_length]) > target_width:
                    tmp_length = tmp_length - 1
                summary_lines.append(summary[:tmp_length])
                summary = summary[tmp_length:]
            summary_lines.append(summary)
            summary = ("\n" + " " * (name_column_width + 3)).join(summary_lines)

        lines.append(f"{name + ' ' * (name_column_width - wcswidth(name))} - {summary}")

    return "\n".join(lines)
