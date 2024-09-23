from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypeVar

from didiator.interface import Handler, Request
from didiator.interface.handlers import HandlerType
from didiator.interface.ioc import Ioc
from dishka import AsyncContainer

R = TypeVar("R", bound=Request[Any])
RRes = TypeVar("RRes")


class DishkaIoc(Ioc):
    def __init__(self, container: AsyncContainer) -> None:
        self._container = container

    @asynccontextmanager
    async def provide(self, handler: HandlerType[R, RRes]) -> AsyncIterator[Handler[R, RRes]]:
        async with self._container() as request_container:
            yield await request_container.get(handler)
