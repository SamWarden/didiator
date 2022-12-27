from collections.abc import Awaitable, Callable, Sequence
import functools
from typing import Any, TypeVar

from didiator.interface.entities.request import Request
from didiator.interface.handlers import HandlerType

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])


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
        if isinstance(handler, type):
            handler = handler()

        return await handler(request, *args, **kwargs)


MiddlewareType = Callable[[HandlerType[R, RRes], R], Awaitable[RRes]]


def wrap_middleware(
    middlewares: Sequence[MiddlewareType[R, RRes]],
    handler: HandlerType[R, RRes],
) -> Callable[..., Awaitable[RRes]]:
    for middleware in reversed(middlewares):
        handler = functools.partial(middleware, handler)

    return handler
