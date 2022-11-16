from typing import Any, TypeVar

from didiator.interface.dispatcher import HandlerType
from didiator.request import Request, Handler

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request)


class Middleware:
    async def __call__(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        return await self._call(handler, request, *args, **kwargs)

    async def _call(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        if isinstance(handler, type) and issubclass(handler, Handler):
            handler = handler()

        return await handler(request, *args, **kwargs)  # noqa: type
        # return await cast(
        #     handler,
        #     Callable[[HandlerType[C, CR] | "Middleware"], Awaitable[CR]],
        # )(command, *args, **kwargs)


# NextMiddlewareType = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]
# MiddlewareType = Union[
#     BaseMiddleware, Callable[[NextMiddlewareType, TelegramObject, Dict[str, Any]], Awaitable[Any]]
# ]
