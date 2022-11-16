import abc
from typing import Any, Generic, TypeVar

from didiator.request import Request, RequestHandler

QRES = TypeVar("QRES")


class Query(Request[QRES], abc.ABC, Generic[QRES]):
    pass


Q = TypeVar("Q", bound=Query[Any])


class QueryHandler(RequestHandler[Q, QRES], abc.ABC, Generic[Q, QRES]):
    @abc.abstractmethod
    async def __call__(self, query: Q) -> QRES:
        ...
