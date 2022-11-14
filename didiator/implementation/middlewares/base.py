from collections.abc import Awaitable, Callable
from typing import cast, ParamSpec, Type, TypeVar

from didiator.implementation.command import Command, CommandHandler

CR = TypeVar("CR")
C = TypeVar("C", bound=Command)
P = ParamSpec("P")

HandlerType = Callable[[C], Awaitable[CR]] | Type[CommandHandler[C, CR]]


class Middleware:
    async def __call__(
        self,
        handler: HandlerType,
        command: C,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> CR:
        return await self._call(handler, command, *args, **kwargs)

    async def _call(
        self,
        handler: HandlerType,
        command: C,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> CR:
        try:
            if issubclass(handler, CommandHandler):
                handler = handler()
        except TypeError:
            pass

        return await handler(command, *args, **kwargs)  # noqa: type
        # return await cast(
        #     handler,
        #     Callable[[HandlerType[C, CR] | "Middleware"], Awaitable[CR]],
        # )(command, *args, **kwargs)


# NextMiddlewareType = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]
# MiddlewareType = Union[
#     BaseMiddleware, Callable[[NextMiddlewareType, TelegramObject, Dict[str, Any]], Awaitable[Any]]
# ]
