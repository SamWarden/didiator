from typing import Any, Awaitable, Callable, ParamSpec, Protocol, Type, TypeVar

from didiator.request import Request, CommandHandler

RES = TypeVar("RES")
R = TypeVar("R", bound=Request[Any])
P = ParamSpec("P")

HandlerType = Callable[[R], Awaitable[RES]] | Type[CommandHandler[R, RES]]

# MiddlewareType = Callable[[HandlerType | "MiddlewareType", C], Awaitable[CR]]
MiddlewareType = Callable[[HandlerType[R, RES], R], Awaitable[RES]]
# MiddlewareType = Callable[[Callable[..., Awaitable[CR]], C], CR]

# x: MiddlewareType[Command[int], str]


class Dispatcher(Protocol):
    @property
    def handlers(self) -> dict[Type[Request[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    @property
    def middlewares(self) -> tuple[MiddlewareType[Any, Any], ...]:
        raise NotImplementedError
