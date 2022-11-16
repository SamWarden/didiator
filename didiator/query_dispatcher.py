from typing import Any, Type, TypeVar

from didiator.interface.dispatcher import HandlerType
from didiator.interface.exceptions import HandlerNotFound, QueryHandlerNotFound
from didiator.interface.query_dispatcher import QueryDispatcher
from didiator.query import Query
from didiator.request_dispatcher import RequestDispatcherImpl

QRES = TypeVar("QRES")
Q = TypeVar("Q", bound=Query[Any])


class QueryDispatcherImpl(RequestDispatcherImpl, QueryDispatcher):
    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QRES]) -> None:
        super()._register_handler(query, handler)

    async def query(self, query: Query[QRES], *args: Any, **kwargs: Any) -> QRES:
        try:
            return await self._handle(query, *args, **kwargs)
        except HandlerNotFound:
            raise QueryHandlerNotFound()
