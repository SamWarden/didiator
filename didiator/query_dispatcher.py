from typing import Any, ParamSpec, Type, TypeVar

from didiator.query import Query
from didiator.interface.command_dispatcher import HandlerType
from didiator.request_dispatcher import RequestDispatcherImpl

QRES = TypeVar("QRES")
Q = TypeVar("Q", bound=Query[Any])
P = ParamSpec("P")


class QueryDispatcherImpl(RequestDispatcherImpl):
    _handlers: dict[Type[Query[Any]], HandlerType[Any, Any]]

    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QRES]) -> None:
        super().register_handler(query, handler)

    # @property
    # def handlers(self) -> dict[Type[Query[Any]], HandlerType]:
    #     return super().handlers

    async def query(self, query: Query[QRES], *args: P.args, **kwargs: P.kwargs) -> QRES:
        return await self._handle(query, *args, **kwargs)
