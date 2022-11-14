import functools
from typing import Any, Awaitable, Callable, ParamSpec, Sequence, Type, TypeVar

from didiator.implementation.command import Command, CommandHandler
from didiator.implementation.middlewares.base import HandlerType, Middleware

CR = TypeVar("CR")
C = TypeVar("C", bound=Command[Any])
P = ParamSpec("P")

# MiddlewareType = Callable[[HandlerType | "MiddlewareType", C], Awaitable[CR]]
MiddlewareType = Callable[[HandlerType[C, CR], C], Awaitable[CR]]
# MiddlewareType = Callable[[Callable[..., Awaitable[CR]], C], CR]

x: MiddlewareType[Command[int], str]

DEFAULT_MIDDLEWARES: tuple[MiddlewareType, ...] = (Middleware(),)


class CommandDispatcherImpl:
    def __init__(self, middlewares: Sequence[MiddlewareType] = ()) -> None:
        self._handlers: dict[Type[Command[Any]], HandlerType[Any, Any]] = {}
        self._middlewares: Sequence[MiddlewareType] = middlewares

    def register_handler(self, command: Type[C], handler: HandlerType[C, CR]) -> None:
        self._handlers[command] = handler

    @property
    def handlers(self) -> dict[Type[Command], HandlerType]:
        return self._handlers

    @property
    def middlewares(self) -> tuple[MiddlewareType, ...]:
        return tuple(self._middlewares)

    async def send(self, command: Command[CR], *args: P.args, **kwargs: P.kwargs) -> CR:
        handler = self._handlers[type(command)]
        # Handler has to be wrapped with at least one middleware to initialize the handler if it is necessary
        middlewares = self._middlewares if self._middlewares else DEFAULT_MIDDLEWARES
        wrapped_handler: Callable[..., Awaitable[CR]] = self._wrap_middleware(middlewares, handler)
        return await wrapped_handler(command, *args, **kwargs)

    @staticmethod
    def _wrap_middleware(
        middlewares: Sequence[MiddlewareType[C, CR]],
        handler: HandlerType[C, CR],
    ) -> Callable[..., Awaitable[CR]]:
        for middleware in reversed(middlewares):
            handler = functools.partial(middleware, handler)

        return handler
