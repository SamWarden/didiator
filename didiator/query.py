import abc
from typing import Any, Generic, TypeVar

from didiator.request import Request, Handler

QRes = TypeVar("QRes")


class Query(Request[QRes], abc.ABC, Generic[QRes]):
    pass


Q = TypeVar("Q", bound=Query[Any])


class QueryHandler(Handler[Q, QRes], abc.ABC, Generic[Q, QRes]):
    @abc.abstractmethod
    async def __call__(self, query: Q) -> QRes:
        ...
