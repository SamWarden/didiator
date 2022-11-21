from typing import Any, Type, TypeVar

from didiator.interface.handlers.request import HandlerType
from didiator.interface.dispatchers.query import QueryDispatcher
from didiator.interface.entities.query import Query
from didiator.interface.exceptions import HandlerNotFound, QueryHandlerNotFound
from didiator.dispatchers.request import RequestDispatcherImpl

QRes = TypeVar("QRes")
Q = TypeVar("Q", bound=Query[Any])


class QueryDispatcherImpl(RequestDispatcherImpl, QueryDispatcher):
    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QRes]) -> None:
        super()._register_handler(query, handler)

    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        try:
            return await self._handle(query, *args, **kwargs)
        except HandlerNotFound:
            raise QueryHandlerNotFound(f"Query handler for {type(query).__name__} query is not registered", query)
