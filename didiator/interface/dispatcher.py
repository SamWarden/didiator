from typing import Any, Awaitable, Callable, ParamSpec, Protocol, Type, TypeVar

from didiator.command import Command, CommandHandler
from didiator.query import Query

CR = TypeVar("CR")
QR = TypeVar("QR")
C = TypeVar("C", bound=Command[Any])
Q = TypeVar("Q", bound=Query[Any])
P = ParamSpec("P")

HandlerType = Callable[[C], Awaitable[CR]] | Type[CommandHandler[C, CR]]

# MiddlewareType = Callable[[HandlerType | "MiddlewareType", C], Awaitable[CR]]
MiddlewareType = Callable[[HandlerType[C, CR], C], Awaitable[CR]]
# MiddlewareType = Callable[[Callable[..., Awaitable[CR]], C], CR]

# x: MiddlewareType[Command[int], str]


class CommandDispatcher(Protocol):
    @property
    def handlers(self) -> dict[Type[Command[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    @property
    def middlewares(self) -> tuple[MiddlewareType[Any, Any], ...]:
        raise NotImplementedError

    def register_handler(self, command: Type[C], handler: HandlerType[C, CR]) -> None:
        raise NotImplementedError

    async def send(self, command: Command[CR], *args: P.args, **kwargs: P.kwargs) -> CR:
        raise NotImplementedError


class QueryDispatcher(Protocol):
    @property
    def handlers(self) -> dict[Type[Command[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    @property
    def middlewares(self) -> tuple[MiddlewareType[Any, Any], ...]:
        raise NotImplementedError

    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QR]) -> None:
        raise NotImplementedError

    async def query(self, query: Query[QR], *args: P.args, **kwargs: P.kwargs) -> QR:
        raise NotImplementedError
