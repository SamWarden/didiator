import abc
import functools
from typing import Any, Awaitable, Callable, ParamSpec, Sequence, Type, TypeVar

from didiator.request import Request
from didiator.middlewares.base import Middleware
from didiator.interface.dispatcher import MiddlewareType, HandlerType

RES = TypeVar("RES")
R = TypeVar("R", bound=Request[Any])
P = ParamSpec("P")


DEFAULT_MIDDLEWARES: tuple[MiddlewareType, ...] = (Middleware(),)


class RequestDispatcherImpl(abc.ABC):
    def __init__(self, middlewares: Sequence[MiddlewareType] = ()) -> None:
        self._handlers: dict[Type[Request[Any]], HandlerType[Any, Any]] = {}
        self._middlewares: Sequence[MiddlewareType] = middlewares

    def register_handler(self, request: Type[R], handler: HandlerType[R, RES]) -> None:
        self._handlers[request] = handler

    @property
    def handlers(self) -> dict[Type[Request[Any]], HandlerType]:
        return self._handlers

    @property
    def middlewares(self) -> tuple[MiddlewareType, ...]:
        return tuple(self._middlewares)

    async def _handle(self, request: Request[RES], *args: P.args, **kwargs: P.kwargs) -> RES:
        handler = self._handlers[type(request)]
        # Handler has to be wrapped with at least one middleware to initialize the handler if it is necessary
        middlewares = self._middlewares if self._middlewares else DEFAULT_MIDDLEWARES
        wrapped_handler: Callable[..., Awaitable[RES]] = self._wrap_middleware(middlewares, handler)
        return await wrapped_handler(request, *args, **kwargs)

    @staticmethod
    def _wrap_middleware(
        middlewares: Sequence[MiddlewareType[R, RES]],
        handler: HandlerType[R, RES],
    ) -> Callable[..., Awaitable[RES]]:
        for middleware in reversed(middlewares):
            handler = functools.partial(middleware, handler)

        return handler
