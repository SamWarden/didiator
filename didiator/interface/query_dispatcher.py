from typing import Any, Protocol, Type, TypeVar

from didiator.interface.dispatcher import Dispatcher, HandlerType
from didiator.query import Query

QRES = TypeVar("QRES")
Q = TypeVar("Q", bound=Query[Any])

# HandlerType = Callable[[Q], Awaitable[QRES]] | Type[RequestHandler[Q, QRES]]


class QueryDispatcher(Dispatcher, Protocol):
    @property
    def handlers(self) -> dict[Type[Query[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QRES]) -> None:
        raise NotImplementedError

    async def query(self, query: Query[QRES], *args: Any, **kwargs: Any) -> QRES:
        raise NotImplementedError
