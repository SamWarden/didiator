import functools
from typing import Any, Awaitable, Callable, ParamSpec, Sequence, Type, TypeVar

from didiator.query import Query
from didiator.middlewares.base import Middleware
from didiator.interface.dispatcher import MiddlewareType, HandlerType

QR = TypeVar("QR")
Q = TypeVar("Q", bound=Query[Any])
P = ParamSpec("P")


DEFAULT_MIDDLEWARES: tuple[MiddlewareType, ...] = (Middleware(),)


class QueryDispatcherImpl:
    def __init__(self, middlewares: Sequence[MiddlewareType] = ()) -> None:
        self._queries: dict[Type[Query[Any]], HandlerType[Any, Any]] = {}
        self._middlewares: Sequence[MiddlewareType] = middlewares

    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QR]) -> None:
        self._queries[query] = handler

    @property
    def handlers(self) -> dict[Type[Query], HandlerType]:
        return self._queries

    @property
    def middlewares(self) -> tuple[MiddlewareType, ...]:
        return tuple(self._middlewares)

    async def query(self, query: Query[QR], *args: P.args, **kwargs: P.kwargs) -> QR:
        handler = self._queries[type(query)]
        # Handler has to be wrapped with at least one middleware to initialize the handler if it is necessary
        middlewares = self._middlewares if self._middlewares else DEFAULT_MIDDLEWARES
        wrapped_handler: Callable[..., Awaitable[QR]] = self._wrap_middleware(middlewares, handler)
        return await wrapped_handler(query, *args, **kwargs)

    @staticmethod
    def _wrap_middleware(
        middlewares: Sequence[MiddlewareType[Q, QR]],
        handler: HandlerType[Q, QR],
    ) -> Callable[..., Awaitable[QR]]:
        for middleware in reversed(middlewares):
            handler = functools.partial(middleware, handler)

        return handler
