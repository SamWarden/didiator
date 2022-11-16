from typing import Any, Type, TypeVar

from didiator.interface.dispatcher import HandlerType
from didiator.interface.exceptions import HandlerNotFound, QueryHandlerNotFound
from didiator.interface.query_dispatcher import QueryDispatcher
from didiator.query import Query
from didiator.request_dispatcher import RequestDispatcherImpl

QRes = TypeVar("QRes")
Q = TypeVar("Q", bound=Query[Any])


class QueryDispatcherImpl(RequestDispatcherImpl, QueryDispatcher):
    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QRes]) -> None:
        super()._register_handler(query, handler)

    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        try:
            return await self._handle(query, *args, **kwargs)
        except HandlerNotFound:
            raise QueryHandlerNotFound()
