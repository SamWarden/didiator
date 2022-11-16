from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, Type, TypeVar

from didiator.middlewares.base import Middleware
from didiator.request import Request, Handler

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])

HandlerType = Callable[[R], Awaitable[RRes]] | Type[Handler[R, RRes]]


class DataAdderMiddlewareMock(Middleware):
    def __init__(self, **kwargs):
        self._additional_kwargs = kwargs

    async def __call__(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        kwargs |= self._additional_kwargs
        return await self._call(handler, request, *args, **kwargs)


class DataRemoverMiddlewareMock(Middleware):
    def __init__(self, *args):
        self._removable_args = args

    async def __call__(
        self,
        handler: HandlerType,
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        kwargs = {key: val for key, val in kwargs.items() if key not in self._removable_args}
        return await self._call(handler, request, *args, **kwargs)
