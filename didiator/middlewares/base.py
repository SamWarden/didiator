from typing import Any, TypeVar

from didiator.request import Request, CommandHandler
from didiator.interface.command_dispatcher import HandlerType

RES = TypeVar("RES")
R = TypeVar("R", bound=Request)


class Middleware:
    async def __call__(
        self,
        handler: HandlerType[R, RES],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RES:
        return await self._call(handler, request, *args, **kwargs)

    async def _call(
        self,
        handler: HandlerType[R, RES],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RES:
        try:
            if issubclass(handler, CommandHandler):
                handler = handler()
        except TypeError:
            pass

        return await handler(request, *args, **kwargs)  # noqa: type
        # return await cast(
        #     handler,
        #     Callable[[HandlerType[C, CR] | "Middleware"], Awaitable[CR]],
        # )(command, *args, **kwargs)


# NextMiddlewareType = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]
# MiddlewareType = Union[
#     BaseMiddleware, Callable[[NextMiddlewareType, TelegramObject, Dict[str, Any]], Awaitable[Any]]
# ]
