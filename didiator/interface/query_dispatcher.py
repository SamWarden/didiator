from typing import Any, Protocol, Type, TypeVar

from didiator.interface.dispatcher import Dispatcher, HandlerType
from didiator.query import Query

QRes = TypeVar("QRes")
Q = TypeVar("Q", bound=Query[Any])

# HandlerType = Callable[[Q], Awaitable[QRes]] | Type[RequestHandler[Q, QRes]]


class QueryDispatcher(Dispatcher, Protocol):
    @property
    def handlers(self) -> dict[Type[Query[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QRes]) -> None:
        raise NotImplementedError

    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        raise NotImplementedError
