from typing import Any, Awaitable, Callable, Protocol, Type, TypeVar

from didiator.interface.entities.request import Request
from didiator.interface.handlers import HandlerType

R = TypeVar("R", bound=Request[Any])
RRes = TypeVar("RRes")

MiddlewareType = Callable[[HandlerType[R, RRes], R], Awaitable[RRes]]


class Dispatcher(Protocol):
    @property
    def handlers(self) -> dict[Type[Request[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    @property
    def middlewares(self) -> tuple[MiddlewareType[Any, Any], ...]:
        raise NotImplementedError
