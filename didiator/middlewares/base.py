from typing import ParamSpec, TypeVar

from didiator.command import Command, CommandHandler
from didiator.interface.dispatcher import HandlerType
from didiator.query import QueryHandler

CR = TypeVar("CR")
C = TypeVar("C", bound=Command)
P = ParamSpec("P")


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
            if issubclass(handler, (CommandHandler, QueryHandler)):
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
