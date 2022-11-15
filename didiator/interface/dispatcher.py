from typing import Any, Awaitable, Callable, ParamSpec, Protocol, Type, TypeVar

from didiator.command import Command, CommandHandler

CR = TypeVar("CR")
C = TypeVar("C", bound=Command)
P = ParamSpec("P")

HandlerType = Callable[[C], Awaitable[CR]] | Type[CommandHandler[C, CR]]

# MiddlewareType = Callable[[HandlerType | "MiddlewareType", C], Awaitable[CR]]
MiddlewareType = Callable[[HandlerType[C, CR], C], Awaitable[CR]]
# MiddlewareType = Callable[[Callable[..., Awaitable[CR]], C], CR]

# x: MiddlewareType[Command[int], str]


class CommandDispatcher(Protocol):
    handlers: dict[Type[Command[Any]], HandlerType[Any, Any]]
    middlewares: tuple[MiddlewareType[Any, Any], ...]

    def register_handler(self, command: Type[C], handler: HandlerType[C, CR]) -> None:
        raise NotImplementedError

    async def send(self, command: Command[CR], *args: P.args, **kwargs: P.kwargs) -> CR:
        raise NotImplementedError
