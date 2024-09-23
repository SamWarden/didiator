from abc import abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from typing import Any, Protocol, TypeVar

from didiator.interface import Handler, Request
from didiator.interface.handlers import HandlerType

R = TypeVar("R", bound=Request[Any])
RRes = TypeVar("RRes")


class Ioc(Protocol):
    @abstractmethod
    @asynccontextmanager
    async def provide(self, handler: HandlerType[R, RRes]) -> AsyncIterator[Handler[R, RRes]]:
        raise NotImplementedError
