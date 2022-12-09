import abc
import functools
from typing import Any, Awaitable, Callable, Sequence, Type, TypeVar

from didiator.interface.entities.request import Request
from didiator.interface.exceptions import HandlerNotFound
from didiator.interface.handlers import HandlerType
from didiator.middlewares.base import Middleware
from didiator.interface.dispatchers.request import Dispatcher, MiddlewareType

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])

DEFAULT_MIDDLEWARES: tuple[MiddlewareType, ...] = (Middleware(),)


class RequestDispatcherImpl(Dispatcher, abc.ABC):
    def __init__(self, middlewares: Sequence[MiddlewareType] = ()) -> None:
        self._handlers: dict[Type[Request[Any]], HandlerType[Any, Any]] = {}
        self._middlewares: Sequence[MiddlewareType] = middlewares

    def _register_handler(self, request: Type[R], handler: HandlerType[R, RRes]) -> None:
        self._handlers[request] = handler

    @property
    def handlers(self) -> dict[Type[Request[Any]], HandlerType]:
        return self._handlers

    @property
    def middlewares(self) -> tuple[MiddlewareType, ...]:
        return tuple(self._middlewares)

    async def _handle(self, request: Request[RRes], *args: Any, **kwargs: Any) -> RRes:
        try:
            handler = self._handlers[type(request)]
        except KeyError:
            raise HandlerNotFound(f"Request handler for {type(request).__name__} request is not registered", request)

        # Handler has to be wrapped with at least one middleware to initialize the handler if it is necessary
        middlewares = self._middlewares if self._middlewares else DEFAULT_MIDDLEWARES
        wrapped_handler: Callable[..., Awaitable[RRes]] = self._wrap_middleware(middlewares, handler)
        return await wrapped_handler(request, *args, **kwargs)

    @staticmethod
    def _wrap_middleware(
        middlewares: Sequence[MiddlewareType[R, RRes]],
        handler: HandlerType[R, RRes],
    ) -> Callable[..., Awaitable[RRes]]:
        for middleware in reversed(middlewares):
            handler = functools.partial(middleware, handler)

        return handler
