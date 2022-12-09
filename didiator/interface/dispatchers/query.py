from typing import Any, Protocol, Type, TypeVar

from didiator.interface.dispatchers.request import Dispatcher
from didiator.interface.entities.query import Query
from didiator.interface.handlers import HandlerType

Q = TypeVar("Q", bound=Query[Any])
QRes = TypeVar("QRes")


class QueryDispatcher(Dispatcher, Protocol):
    @property
    def handlers(self) -> dict[Type[Query[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    def register_handler(self, query: Type[Q], handler: HandlerType[Q, QRes]) -> None:
        raise NotImplementedError

    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        raise NotImplementedError
