from typing import ParamSpec, TypeVar

from didiator.request import Request, RequestHandler
from didiator.interface.command_dispatcher import HandlerType

RES = TypeVar("RES")
R = TypeVar("R", bound=Request)
P = ParamSpec("P")


class Middleware:
    async def __call__(
        self,
        handler: HandlerType,
        request: R,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> RES:
        return await self._call(handler, request, *args, **kwargs)

    async def _call(
        self,
        handler: HandlerType,
        request: R,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> RES:
        try:
            if issubclass(handler, RequestHandler):
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
