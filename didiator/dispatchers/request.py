import abc
from typing import Any, Awaitable, Callable, Sequence, Type, TypeVar

from didiator.interface.entities.request import Request
from didiator.interface.exceptions import HandlerNotFound
from didiator.interface.handlers import HandlerType
from didiator.middlewares.base import Middleware, MiddlewareType, wrap_middleware
from didiator.interface.dispatchers.request import Dispatcher

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])

DEFAULT_MIDDLEWARES: tuple[MiddlewareType[Request[Any], Any], ...] = (Middleware(),)


class DispatcherImpl(Dispatcher, abc.ABC):
    def __init__(self, middlewares: Sequence[MiddlewareType[Request[Any], Any]] = ()) -> None:
        self._handlers: dict[Type[Request[Any]], HandlerType[Request[Any], Any]] = {}
        self._middlewares: Sequence[MiddlewareType[Request[Any], Any]] = middlewares

    def _register_handler(self, request: Type[R], handler: HandlerType[R, RRes]) -> None:
        self._handlers[request] = handler

    @property
    def handlers(self) -> dict[Type[Request[Any]], HandlerType[Request[Any], Any]]:
        return self._handlers

    @property
    def middlewares(self) -> tuple[MiddlewareType[Request[Any], Any], ...]:
        return tuple(self._middlewares)

    async def _handle(self, request: Request[RRes], *args: Any, **kwargs: Any) -> RRes:
        try:
            handler = self._handlers[type(request)]
        except KeyError:
            raise HandlerNotFound(f"Request handler for {type(request).__name__} request is not registered", request)

        # Handler has to be wrapped with at least one middleware to initialize the handler if it is necessary
        middlewares: Sequence[MiddlewareType[Any, Any]] = self._middlewares if self._middlewares else DEFAULT_MIDDLEWARES
        wrapped_handler: Callable[..., Awaitable[RRes]] = self._wrap_middleware(middlewares, handler)
        return await wrapped_handler(request, *args, **kwargs)

    @staticmethod
    def _wrap_middleware(
        middlewares: Sequence[MiddlewareType[R, Any]],
        handler: HandlerType[R, Any],
    ) -> Callable[..., Awaitable[Any]]:
        return wrap_middleware(middlewares, handler)
