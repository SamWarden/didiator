from typing import Any, Protocol, Type, TypeVar

from didiator.interface.entities.request import Request
from didiator.interface.handlers import HandlerType
from didiator.middlewares.base import MiddlewareType

Self = TypeVar("Self", bound="Dispatcher")
R = TypeVar("R", bound=Request[Any])
RRes = TypeVar("RRes")


class Dispatcher(Protocol):
    @property
    def handlers(self) -> dict[Type[Request[Any]], HandlerType[Request[Any], Any]]:
        raise NotImplementedError

    @property
    def middlewares(self) -> tuple[MiddlewareType[Request[Any], Any], ...]:
        raise NotImplementedError

    def copy(self: Self) -> Self:
        raise NotImplementedError
